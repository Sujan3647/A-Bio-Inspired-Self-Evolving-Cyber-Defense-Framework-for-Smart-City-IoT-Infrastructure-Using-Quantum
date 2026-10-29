/**
 * ImmunoGrid — Solidity Unit Tests
 * Tests all 4 contracts: ImmunoGrid, KeyRegistry, FL, Honeypot
 *
 * Run: npx hardhat test
 */

const { expect }         = require("chai");
const { ethers }         = require("hardhat");
const { time }           = require("@nomicfoundation/hardhat-network-helpers");

// ── Helpers ───────────────────────────────────────────────────────────────────

const toBytes32 = (str) => ethers.keccak256(ethers.toUtf8Bytes(str));

// ── ImmunoGrid Main Contract Tests ────────────────────────────────────────────

describe("ImmunoGrid — Attack Registry + Morphogenesis", () => {

  let immunoGrid, owner, node1, node2;

  beforeEach(async () => {
    [owner, node1, node2] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ImmunoGrid");
    immunoGrid = await Factory.deploy();
    await immunoGrid.waitForDeployment();
  });

  // ── Deployment ─────────────────────────────────────────────────────────────

  describe("Deployment", () => {
    it("should set owner correctly", async () => {
      expect(await immunoGrid.owner()).to.equal(owner.address);
    });

    it("should initialize topology correctly", async () => {
      const topo = await immunoGrid.getTopology();
      expect(topo.fpSensitivityBps).to.equal(9200n);
      expect(topo.honeypotCount).to.equal(5n);
      expect(topo.morphogenesisCount).to.equal(0n);
    });

    it("should authorize owner as first node", async () => {
      const nodeInfo = await immunoGrid.authorizedNodes(owner.address);
      expect(nodeInfo.isAuthorized).to.be.true;
      expect(nodeInfo.isActive).to.be.true;
    });
  });

  // ── Node Authorization ─────────────────────────────────────────────────────

  describe("Node Authorization", () => {
    it("should authorize a new node", async () => {
      await immunoGrid.authorizeNode(node1.address, "SecurityOrg");
      const nodeInfo = await immunoGrid.authorizedNodes(node1.address);
      expect(nodeInfo.isAuthorized).to.be.true;
      expect(nodeInfo.orgName).to.equal("SecurityOrg");
    });

    it("should reject unauthorized node recording", async () => {
      await expect(
        immunoGrid.connect(node1).recordAttack(
          "spoofing", "dev-001", "traffic", 2, "quantum", "raw data"
        )
      ).to.be.revertedWith("ImmunoGrid: Not an authorized node");
    });

    it("should revoke a node", async () => {
      await immunoGrid.authorizeNode(node1.address, "Org1");
      await immunoGrid.revokeNode(node1.address);
      const nodeInfo = await immunoGrid.authorizedNodes(node1.address);
      expect(nodeInfo.isAuthorized).to.be.false;
    });
  });

  // ── Attack Recording ───────────────────────────────────────────────────────

  describe("recordAttack", () => {
    it("should record a spoofing attack and emit event", async () => {
      const tx = await immunoGrid.recordAttack(
        "spoofing", "traffic-sensor-001", "traffic", 2, "quantum_fingerprint", "raw"
      );
      const receipt = await tx.wait();

      // Check event
      const event = receipt.logs.find(
        (l) => l.fragment?.name === "AttackRecorded"
      );
      expect(event).to.not.be.undefined;

      // Check total attacks incremented
      expect(await immunoGrid.totalAttacks()).to.equal(1n);
    });

    it("should increment totalAttacks on each record", async () => {
      await immunoGrid.recordAttack("spoofing",       "d1", "traffic",  2, "quantum", "r");
      await immunoGrid.recordAttack("ddos",           "d2", "hospital", 3, "ai_brain","r");
      await immunoGrid.recordAttack("data_poisoning", "d3", "water",    1, "honeypot","r");
      expect(await immunoGrid.totalAttacks()).to.equal(3n);
    });

    it("should store attack record retrievable by ID", async () => {
      const tx = await immunoGrid.recordAttack(
        "spoofing", "dev-001", "traffic", 2, "quantum", "raw_data"
      );
      const receipt = await tx.wait();
      const event = receipt.logs.find(l => l.fragment?.name === "AttackRecorded");
      const recordId = event.args[0];

      const record = await immunoGrid.getAttackRecord(recordId);
      expect(record.attackType).to.equal("spoofing");
      expect(record.sector).to.equal("traffic");
      expect(record.deviceId).to.equal("dev-001");
    });

    it("should reject invalid severity", async () => {
      await expect(
        immunoGrid.recordAttack("spoofing", "d1", "traffic", 4, "quantum", "r")
      ).to.be.revertedWith("ImmunoGrid: Invalid severity level");
    });
  });

  // ── Attack Pattern Recognition ─────────────────────────────────────────────

  describe("isPatternKnown", () => {
    it("should return 0 for unknown pattern", async () => {
      const count = await immunoGrid.isPatternKnown("spoofing", "traffic");
      expect(count).to.equal(0n);
    });

    it("should count repeated patterns", async () => {
      await immunoGrid.recordAttack("spoofing", "d1", "traffic", 2, "quantum", "r");
      await immunoGrid.recordAttack("spoofing", "d2", "traffic", 2, "quantum", "r");
      await immunoGrid.recordAttack("ddos",     "d3", "traffic", 3, "ai",     "r");

      const spoofCount = await immunoGrid.isPatternKnown("spoofing", "traffic");
      const ddosCount  = await immunoGrid.isPatternKnown("ddos",     "traffic");
      expect(spoofCount).to.equal(2n);
      expect(ddosCount).to.equal(1n);
    });
  });

  // ── Morphogenesis ──────────────────────────────────────────────────────────

  describe("Morphogenesis", () => {
    it("should spawn honeypots on spoofing attack", async () => {
      const topoBefore = await immunoGrid.getTopology();
      await immunoGrid.recordAttack("spoofing", "dev-001", "traffic", 2, "quantum", "r");
      const topoAfter = await immunoGrid.getTopology();

      expect(topoAfter.honeypotCount).to.be.greaterThan(topoBefore.honeypotCount);
      expect(topoAfter.morphogenesisCount).to.equal(1n);
    });

    it("should increase FP sensitivity on spoofing", async () => {
      const topoBefore = await immunoGrid.getTopology();
      await immunoGrid.recordAttack("spoofing", "dev-001", "traffic", 2, "quantum", "r");
      const topoAfter = await immunoGrid.getTopology();

      expect(topoAfter.fpSensitivityBps).to.be.lessThan(topoBefore.fpSensitivityBps);
    });

    it("should isolate sector on critical DDoS", async () => {
      await immunoGrid.recordAttack("ddos", "dev-002", "hospital", 3, "ai_brain", "r");
      const isIsolated = await immunoGrid.isSectorIsolated("hospital");
      expect(isIsolated).to.be.true;
    });

    it("should quarantine device on high spoofing", async () => {
      await immunoGrid.recordAttack("spoofing", "dev-003", "water", 2, "quantum", "r");
      const isQrt = await immunoGrid.isDeviceQuarantined("dev-003");
      expect(isQrt).to.be.true;
    });

    it("should emit MorphogenesisExecuted event", async () => {
      await expect(
        immunoGrid.recordAttack("spoofing", "dev-004", "power", 2, "quantum", "r")
      ).to.emit(immunoGrid, "MorphogenesisExecuted");
    });

    it("should restore sector after isolation", async () => {
      await immunoGrid.recordAttack("ddos", "dev-005", "metro", 3, "ai", "r");
      expect(await immunoGrid.isSectorIsolated("metro")).to.be.true;
      await immunoGrid.restoreSector("metro");
      expect(await immunoGrid.isSectorIsolated("metro")).to.be.false;
    });
  });

  // ── Stats ──────────────────────────────────────────────────────────────────

  describe("getStats", () => {
    it("should return correct stats", async () => {
      await immunoGrid.recordAttack("spoofing", "d1", "traffic", 2, "q", "r");
      await immunoGrid.recordAttack("ddos",     "d2", "hospital",3, "ai","r");

      const [attacks, morph, honeypots, fpBps, version] = await immunoGrid.getStats();
      expect(attacks).to.equal(2n);
      expect(morph).to.be.greaterThan(0n);
      expect(honeypots).to.be.greaterThan(5n);
      expect(version).to.equal(1n);
    });
  });
});

// ── Key Registry Tests ────────────────────────────────────────────────────────

describe("ImmunoGridKeyRegistry — PQC Key Management", () => {
  let keyRegistry, owner, addr1;

  beforeEach(async () => {
    [owner, addr1] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ImmunoGridKeyRegistry");
    keyRegistry = await Factory.deploy();
    await keyRegistry.waitForDeployment();
  });

  describe("registerDevice", () => {
    it("should register a device with valid keys", async () => {
      const kemHash = toBytes32("kyber-pubkey-device-001");
      const sigHash = toBytes32("dilithium-pubkey-device-001");

      await keyRegistry.registerDevice("dev-001", kemHash, sigHash);

      const keys = await keyRegistry.deviceKeys("dev-001");
      expect(keys.kemKeyHash).to.equal(kemHash);
      expect(keys.sigKeyHash).to.equal(sigHash);
      expect(keys.isActive).to.be.true;
    });

    it("should reject duplicate registration", async () => {
      const h = toBytes32("key");
      await keyRegistry.registerDevice("dev-002", h, h);
      await expect(
        keyRegistry.registerDevice("dev-002", h, h)
      ).to.be.revertedWith("KeyRegistry: Device already registered");
    });

    it("should reject zero key hash", async () => {
      await expect(
        keyRegistry.registerDevice("dev-003", ethers.ZeroHash, toBytes32("sig"))
      ).to.be.revertedWith("KeyRegistry: Invalid KEM key hash");
    });
  });

  describe("verifyKey", () => {
    it("should verify matching keys as valid", async () => {
      const kemHash = toBytes32("kem-key");
      const sigHash = toBytes32("sig-key");
      await keyRegistry.registerDevice("dev-004", kemHash, sigHash);

      const [valid, reason] = await keyRegistry.verifyKey("dev-004", kemHash, sigHash);
      expect(valid).to.be.true;
      expect(reason).to.equal("Valid");
    });

    it("should reject unknown device", async () => {
      const [valid, reason] = await keyRegistry.verifyKey(
        "unknown-device", toBytes32("k"), toBytes32("s")
      );
      expect(valid).to.be.false;
      expect(reason).to.equal("Device not registered");
    });

    it("should reject mismatched KEM key", async () => {
      const kemHash = toBytes32("kem");
      const sigHash = toBytes32("sig");
      await keyRegistry.registerDevice("dev-005", kemHash, sigHash);

      const [valid, reason] = await keyRegistry.verifyKey(
        "dev-005", toBytes32("wrong-kem"), sigHash
      );
      expect(valid).to.be.false;
      expect(reason).to.equal("KEM key mismatch — possible IMPOSTOR");
    });

    it("should reject revoked key", async () => {
      const h = toBytes32("k");
      await keyRegistry.registerDevice("dev-006", h, h);
      await keyRegistry.revokeKey("dev-006", "compromised");

      const [valid, reason] = await keyRegistry.verifyKey("dev-006", h, h);
      expect(valid).to.be.false;
      expect(reason).to.equal("Key revoked");
    });
  });

  describe("rotateKey", () => {
    it("should rotate key and update hash", async () => {
      const oldKem = toBytes32("old-kem");
      const oldSig = toBytes32("old-sig");
      await keyRegistry.registerDevice("dev-007", oldKem, oldSig);

      const newKem = toBytes32("new-kem");
      const newSig = toBytes32("new-sig");
      await keyRegistry.rotateKey("dev-007", newKem, newSig, "scheduled");

      const [valid] = await keyRegistry.verifyKey("dev-007", newKem, newSig);
      expect(valid).to.be.true;

      const [oldValid] = await keyRegistry.verifyKey("dev-007", oldKem, oldSig);
      expect(oldValid).to.be.false;
    });

    it("should increment rotation count", async () => {
      const h = toBytes32("k");
      await keyRegistry.registerDevice("dev-008", h, h);
      const newH = toBytes32("new-k");
      await keyRegistry.rotateKey("dev-008", newH, newH, "scheduled");

      const keys = await keyRegistry.deviceKeys("dev-008");
      expect(keys.rotationCount).to.equal(1n);
    });
  });

  describe("bulkRegister", () => {
    it("should register multiple devices in one tx", async () => {
      const ids = ["bulk-1", "bulk-2", "bulk-3"];
      const hashes = ids.map(id => toBytes32(id + "-key"));

      await keyRegistry.bulkRegister(ids, hashes, hashes);
      expect(await keyRegistry.getDeviceCount()).to.equal(3n);
    });
  });
});

// ── FL Registry Tests ─────────────────────────────────────────────────────────

describe("ImmunoGridFL — Model Provenance", () => {
  let flRegistry, owner;

  beforeEach(async () => {
    [owner] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ImmunoGridFL");
    flRegistry = await Factory.deploy();
    await flRegistry.waitForDeployment();
  });

  describe("commitModelVersion", () => {
    it("should commit model version and emit event", async () => {
      const modelHash = toBytes32("model-round-1");
      const gradHash  = toBytes32("grads-round-1");

      await expect(
        flRegistry.commitModelVersion(modelHash, gradHash, 9720, 500, 492, 1200)
      ).to.emit(flRegistry, "ModelVersionCommitted");

      expect(await flRegistry.currentRound()).to.equal(1n);
    });

    it("should increment round number", async () => {
      for (let i = 1; i <= 3; i++) {
        await flRegistry.commitModelVersion(
          toBytes32(`model-${i}`), toBytes32(`grads-${i}`),
          9700 + i * 10, 500, 490, 100
        );
      }
      expect(await flRegistry.currentRound()).to.equal(3n);
    });

    it("should reject duplicate model hash (replay prevention)", async () => {
      const h = toBytes32("model-v1");
      await flRegistry.commitModelVersion(h, h, 9500, 490, 488, 100);
      await expect(
        flRegistry.commitModelVersion(h, toBytes32("grads-2"), 9600, 495, 490, 110)
      ).to.be.revertedWith("FLRegistry: Duplicate model hash (replay?)");
    });

    it("should reject accuracy > 100%", async () => {
      await expect(
        flRegistry.commitModelVersion(
          toBytes32("m"), toBytes32("g"), 10001, 500, 490, 100
        )
      ).to.be.revertedWith("FLRegistry: Accuracy > 100%");
    });
  });

  describe("verifyModel", () => {
    it("should return true for committed model", async () => {
      const h = toBytes32("model-verified");
      await flRegistry.commitModelVersion(h, toBytes32("g"), 9800, 500, 495, 200);
      expect(await flRegistry.verifyModel(h)).to.be.true;
    });

    it("should return false for unknown model", async () => {
      expect(await flRegistry.verifyModel(toBytes32("unknown"))).to.be.false;
    });
  });

  describe("flagPoisoning", () => {
    it("should mark round as poisoned", async () => {
      await flRegistry.commitModelVersion(
        toBytes32("m1"), toBytes32("g1"), 9500, 500, 490, 100
      );
      await flRegistry.flagPoisoning(1, "malicious-device-007");

      const version = await flRegistry.getModelVersion(1);
      expect(version.poisoningDetected).to.be.true;
    });
  });

  describe("recordContribution", () => {
    it("should record client contribution", async () => {
      await flRegistry.commitModelVersion(
        toBytes32("m"), toBytes32("g"), 9700, 490, 488, 100
      );
      await flRegistry.recordContribution(
        "device-001", toBytes32("gradient-hash"), 500
      );
      expect(await flRegistry.getContributionCount(1)).to.equal(1n);
    });
  });
});

// ── Honeypot Registry Tests ───────────────────────────────────────────────────

describe("ImmunoGridHoneypot — Threat Intelligence", () => {
  let honeypot, owner;

  beforeEach(async () => {
    [owner] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ImmunoGridHoneypot");
    honeypot = await Factory.deploy();
    await honeypot.waitForDeployment();
  });

  describe("fileReport", () => {
    it("should file report and emit event", async () => {
      const attackerHash = toBytes32("attacker-001");
      const behaviorHash = toBytes32("behavior-sig");

      await expect(
        honeypot.fileReport(
          attackerHash, "spoofing", "traffic", 5, behaviorHash, 12
        )
      ).to.emit(honeypot, "HoneypotReportFiled");

      expect(await honeypot.totalReports()).to.equal(1n);
    });

    it("should create attacker profile on first report", async () => {
      const attackerHash = toBytes32("attacker-new");
      await honeypot.fileReport(
        attackerHash, "ddos", "hospital", 8, toBytes32("bh"), 20
      );

      const [known, attempts] = await honeypot.isKnownAttacker(attackerHash);
      expect(known).to.be.true;
      expect(attempts).to.equal(8n);
    });

    it("should update profile on repeated attacker", async () => {
      const attackerHash = toBytes32("repeat-attacker");
      await honeypot.fileReport(attackerHash, "spoofing", "traffic", 3, toBytes32("b1"), 6);
      await honeypot.fileReport(attackerHash, "spoofing", "water",   5, toBytes32("b2"), 10);

      const [known, attempts] = await honeypot.isKnownAttacker(attackerHash);
      expect(known).to.be.true;
      expect(attempts).to.equal(8n);  // 3 + 5
    });

    it("should accumulate AI samples", async () => {
      await honeypot.fileReport(toBytes32("a1"), "spoofing", "traffic", 3, toBytes32("b"), 15);
      await honeypot.fileReport(toBytes32("a2"), "ddos",     "hospital",5, toBytes32("c"), 25);

      expect(await honeypot.totalAiSamples()).to.equal(40n);
    });
  });

  describe("isKnownAttacker", () => {
    it("should return false for unknown attacker", async () => {
      const [known] = await honeypot.isKnownAttacker(toBytes32("unknown"));
      expect(known).to.be.false;
    });
  });

  describe("getStats", () => {
    it("should return correct stats after reports", async () => {
      await honeypot.fileReport(toBytes32("a1"), "spoofing", "traffic", 3, toBytes32("b1"), 10);
      await honeypot.fileReport(toBytes32("a2"), "ddos", "hospital", 2, toBytes32("b2"), 5);

      const [reports, samples, attackers, active] = await honeypot.getStats();
      expect(reports).to.equal(2n);
      expect(samples).to.equal(15n);
      expect(attackers).to.equal(2n);
    });
  });
});
