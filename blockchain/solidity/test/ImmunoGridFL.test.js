/**
 * ImmunoGrid FL + Honeypot + Oracle — Unit Tests
 * Covers remaining contracts not tested in ImmunoGrid.test.js
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

const h = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));

// ── ImmunoGridFL Tests ─────────────────────────────────────────────────────────

describe("ImmunoGridFL — Federated Learning Model Registry", () => {
  let fl, owner, node1;

  beforeEach(async () => {
    [owner, node1] = await ethers.getSigners();
    const F = await ethers.getContractFactory("ImmunoGridFL");
    fl = await F.deploy();
    await fl.waitForDeployment();
  });

  describe("Deployment", () => {
    it("sets owner", async () => {
      expect(await fl.owner()).to.equal(owner.address);
    });
    it("starts at round 0", async () => {
      expect(await fl.currentRound()).to.equal(0n);
    });
  });

  describe("commitModelVersion", () => {
    it("increments round number", async () => {
      await fl.commitModelVersion(h("m1"), h("g1"), 9500, 800, 490, 100);
      expect(await fl.currentRound()).to.equal(1n);
    });

    it("stores model data correctly", async () => {
      const mh = h("model-round-1");
      await fl.commitModelVersion(mh, h("g1"), 9720, 500, 492, 1200);
      const v = await fl.getModelVersion(1);
      expect(v.modelHash).to.equal(mh);
      expect(v.accuracy).to.equal(9720n);
      expect(v.participants).to.equal(492n);
      expect(v.imaginationsCount).to.equal(1200n);
      expect(v.poisoningDetected).to.be.false;
    });

    it("emits ModelVersionCommitted event", async () => {
      await expect(
        fl.commitModelVersion(h("m"), h("g"), 9800, 400, 495, 200)
      ).to.emit(fl, "ModelVersionCommitted");
    });

    it("emits ImaginationsRecorded event", async () => {
      await expect(
        fl.commitModelVersion(h("m2"), h("g2"), 9600, 600, 488, 500)
      ).to.emit(fl, "ImaginationsRecorded");
    });

    it("rejects duplicate model hash (replay protection)", async () => {
      const mh = h("unique-model");
      await fl.commitModelVersion(mh, h("g"), 9500, 700, 490, 100);
      await expect(
        fl.commitModelVersion(mh, h("g2"), 9600, 600, 491, 110)
      ).to.be.revertedWith("FLRegistry: Duplicate model hash (replay?)");
    });

    it("rejects accuracy > 100%", async () => {
      await expect(
        fl.commitModelVersion(h("m"), h("g"), 10001, 500, 490, 100)
      ).to.be.revertedWith("FLRegistry: Accuracy > 100%");
    });

    it("accumulates total imaginations", async () => {
      await fl.commitModelVersion(h("m1"), h("g1"), 9500, 700, 490, 300);
      await fl.commitModelVersion(h("m2"), h("g2"), 9600, 600, 492, 500);
      expect(await fl.totalImaginations()).to.equal(800n);
    });
  });

  describe("verifyModel", () => {
    it("returns true for committed model", async () => {
      const mh = h("verified-model");
      await fl.commitModelVersion(mh, h("g"), 9700, 500, 490, 100);
      expect(await fl.verifyModel(mh)).to.be.true;
    });

    it("returns false for unknown model", async () => {
      expect(await fl.verifyModel(h("unknown-model"))).to.be.false;
    });
  });

  describe("flagPoisoning", () => {
    it("marks round as poisoned and emits event", async () => {
      await fl.commitModelVersion(h("m"), h("g"), 9400, 800, 488, 100);
      await expect(
        fl.flagPoisoning(1, "byzantine-device-007")
      ).to.emit(fl, "PoisoningDetected");

      const v = await fl.getModelVersion(1);
      expect(v.poisoningDetected).to.be.true;
    });

    it("rejects invalid round number", async () => {
      await expect(
        fl.flagPoisoning(99, "device")
      ).to.be.revertedWith("FLRegistry: Round not found");
    });
  });

  describe("recordContribution", () => {
    it("records client gradient contribution", async () => {
      await fl.commitModelVersion(h("m"), h("g"), 9600, 600, 490, 100);
      await fl.recordContribution("device-001", h("gradient-hash"), 500);
      expect(await fl.getContributionCount(1)).to.equal(1n);
    });

    it("accumulates multiple contributions", async () => {
      await fl.commitModelVersion(h("m"), h("g"), 9700, 500, 490, 100);
      for (let i = 0; i < 5; i++) {
        await fl.recordContribution(`device-${i}`, h(`grad-${i}`), 100);
      }
      expect(await fl.getContributionCount(1)).to.equal(5n);
    });

    it("rejects zero gradient hash", async () => {
      await fl.commitModelVersion(h("m"), h("g"), 9700, 500, 490, 100);
      await expect(
        fl.recordContribution("device", ethers.ZeroHash, 100)
      ).to.be.revertedWith("FLRegistry: Invalid gradient hash");
    });
  });

  describe("getLatestAccuracy", () => {
    it("returns latest round accuracy", async () => {
      await fl.commitModelVersion(h("m1"), h("g1"), 9500, 700, 490, 100);
      await fl.commitModelVersion(h("m2"), h("g2"), 9750, 450, 495, 150);
      const [acc, round] = await fl.getLatestAccuracy();
      expect(acc).to.equal(9750n);
      expect(round).to.equal(2n);
    });

    it("returns 0 before any round", async () => {
      const [acc, round] = await fl.getLatestAccuracy();
      expect(acc).to.equal(0n);
      expect(round).to.equal(0n);
    });
  });

  describe("getStats", () => {
    it("returns correct stats after 3 rounds", async () => {
      await fl.commitModelVersion(h("m1"), h("g1"), 9500, 700, 490, 200);
      await fl.commitModelVersion(h("m2"), h("g2"), 9700, 500, 492, 300);
      await fl.commitModelVersion(h("m3"), h("g3"), 9800, 400, 495, 400);

      const [round, imag, acc, poisoned] = await fl.getStats();
      expect(round).to.equal(3n);
      expect(imag).to.equal(900n);
      expect(acc).to.equal(9800n);
      expect(poisoned).to.be.false;
    });
  });
});

// ── ImmunoGridHoneypot Additional Tests ────────────────────────────────────────

describe("ImmunoGridHoneypot — Extended Tests", () => {
  let honeypot, owner;

  beforeEach(async () => {
    [owner] = await ethers.getSigners();
    const F = await ethers.getContractFactory("ImmunoGridHoneypot");
    honeypot = await F.deploy();
    await honeypot.waitForDeployment();
  });

  it("generates unique report IDs", async () => {
    const r1 = await honeypot.fileReport.staticCall(h("a1"), "spoofing", "traffic", 3, h("b1"), 6);
    const r2 = await honeypot.fileReport.staticCall(h("a2"), "ddos", "hospital", 5, h("b2"), 10);
    expect(r1).to.not.equal(r2);
  });

  it("emits NewAttackerProfiled on first report", async () => {
    await expect(
      honeypot.fileReport(h("new-attacker"), "spoofing", "traffic", 3, h("b"), 6)
    ).to.emit(honeypot, "NewAttackerProfiled");
  });

  it("emits ThreatIntelUpdated on repeat attacker", async () => {
    const attackerHash = h("repeat-actor");
    await honeypot.fileReport(attackerHash, "spoofing", "traffic", 3, h("b1"), 6);
    await expect(
      honeypot.fileReport(attackerHash, "ddos", "hospital", 5, h("b2"), 10)
    ).to.emit(honeypot, "ThreatIntelUpdated");
  });

  it("tracks total AI samples correctly", async () => {
    await honeypot.fileReport(h("a1"), "spoofing", "traffic", 3, h("b1"), 15);
    await honeypot.fileReport(h("a2"), "ddos", "hospital", 5, h("b2"), 25);
    await honeypot.fileReport(h("a3"), "ransomware", "power", 8, h("b3"), 40);
    expect(await honeypot.totalAiSamples()).to.equal(80n);
  });

  it("retrieves report by ID", async () => {
    const tx = await honeypot.fileReport(h("actor"), "spoofing", "traffic", 4, h("beh"), 8);
    const receipt = await tx.wait();
    const event = receipt.logs.find(l => l.fragment?.name === "HoneypotReportFiled");
    const reportId = event.args[0];

    const report = await honeypot.getReport(reportId);
    expect(report.attackType).to.equal("spoofing");
    expect(report.sector).to.equal("traffic");
    expect(report.interactionCount).to.equal(4n);
  });

  it("rejects getReport for unknown ID", async () => {
    await expect(honeypot.getReport(h("nonexistent"))).to.be.revertedWith("Report not found");
  });
});

// ── ImmunoGridOracle Tests ─────────────────────────────────────────────────────

describe("ImmunoGridOracle — Threat Intelligence Feed", () => {
  let oracle, immunoGrid, owner, subscriber;

  beforeEach(async () => {
    [owner, subscriber] = await ethers.getSigners();
    const IGF = await ethers.getContractFactory("ImmunoGrid");
    immunoGrid = await IGF.deploy();
    await immunoGrid.waitForDeployment();

    const OF = await ethers.getContractFactory("ImmunoGridOracle");
    oracle = await OF.deploy(await immunoGrid.getAddress());
    await oracle.waitForDeployment();
    await oracle.subscribe();  // owner subscribes
  });

  describe("Deployment", () => {
    it("initializes with zero global threat", async () => {
      const [score, level] = await oracle.getGlobalThreat();
      expect(score).to.equal(0n);
      expect(level).to.equal(0);
    });

    it("all sectors start safe", async () => {
      for (const sector of ["traffic","hospital","water","power"]) {
        const [safe] = await oracle.isSectorSafe(sector);
        expect(safe).to.be.true;
      }
    });
  });

  describe("updateSectorThreat", () => {
    it("updates threat level correctly", async () => {
      await oracle.updateSectorThreat("hospital", 7000, 5, "spoofing");
      const tl = await oracle.sectorThreat("hospital");
      expect(tl.score).to.equal(7000n);
      expect(tl.level).to.equal(3);  // HIGH
      expect(tl.underActiveAttack).to.be.true;
    });

    it("sets correct threat levels: 0=NONE, 1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL", async () => {
      const cases = [
        { score: 0,    level: 0 },
        { score: 1000, level: 1 },
        { score: 3000, level: 2 },
        { score: 6000, level: 3 },
        { score: 9000, level: 4 },
      ];
      for (const { score, level } of cases) {
        await oracle.updateSectorThreat("traffic", score, 0, "none");
        const [, tl] = await oracle.isSectorSafe("traffic");
        // LOW (1) is still "safe"
        const [safe] = await oracle.isSectorSafe("traffic");
        if (level <= 1) expect(safe).to.be.true;
        else            expect(safe).to.be.false;
      }
    });

    it("emits CriticalAlert on level 4", async () => {
      await expect(
        oracle.updateSectorThreat("water", 9500, 10, "ransomware")
      ).to.emit(oracle, "CriticalAlert");
    });

    it("emits ThreatLevelUpdated event", async () => {
      await expect(
        oracle.updateSectorThreat("power", 5000, 3, "ddos")
      ).to.emit(oracle, "ThreatLevelUpdated");
    });

    it("rejects score > 10000", async () => {
      await expect(
        oracle.updateSectorThreat("traffic", 10001, 0, "none")
      ).to.be.revertedWith("Oracle: Score out of range");
    });

    it("updates global threat score", async () => {
      await oracle.updateSectorThreat("hospital", 8000, 5, "ddos");
      const [globalScore] = await oracle.getGlobalThreat();
      expect(globalScore).to.be.greaterThan(0n);
    });
  });

  describe("updateDeviceTrust", () => {
    it("marks device as trusted when score >= 9200", async () => {
      await oracle.updateDeviceTrust("dev-trusted", 9500, 9800);
      const [trusted, score] = await oracle.isDeviceTrusted("dev-trusted");
      expect(trusted).to.be.true;
      expect(score).to.equal(9500n);
    });

    it("marks device as untrusted when score < 9200", async () => {
      await oracle.updateDeviceTrust("dev-suspect", 7000, 7500);
      const [trusted] = await oracle.isDeviceTrusted("dev-suspect");
      expect(trusted).to.be.false;
    });

    it("returns false for unknown device", async () => {
      const [trusted] = await oracle.isDeviceTrusted("unknown-device");
      expect(trusted).to.be.false;
    });

    it("emits DeviceTrustUpdated event", async () => {
      await expect(
        oracle.updateDeviceTrust("dev-001", 9700, 9850)
      ).to.emit(oracle, "DeviceTrustUpdated");
    });
  });

  describe("getAllSectorThreats", () => {
    it("returns data for all 8 sectors", async () => {
      const [sectors, levels, scores] = await oracle.getAllSectorThreats();
      expect(sectors.length).to.equal(8);
      expect(levels.length).to.equal(8);
      expect(scores.length).to.equal(8);
    });

    it("reflects updated threats correctly", async () => {
      await oracle.updateSectorThreat("metro", 6000, 3, "spoofing");
      const [sectors, levels] = await oracle.getAllSectorThreats();
      const metroIdx = sectors.indexOf("metro");
      expect(metroIdx).to.not.equal(-1);
      expect(levels[metroIdx]).to.equal(3);
    });
  });

  describe("Subscription", () => {
    it("subscriber can update threat", async () => {
      await oracle.connect(subscriber).subscribe();
      await expect(
        oracle.connect(subscriber).updateSectorThreat("traffic", 3000, 2, "ddos")
      ).to.not.be.reverted;
    });

    it("non-subscriber cannot update threat", async () => {
      const [,,nonSub] = await ethers.getSigners();
      await expect(
        oracle.connect(nonSub).updateSectorThreat("traffic", 3000, 2, "ddos")
      ).to.be.revertedWith("Oracle: Not authorized");
    });

    it("tracks subscriber count", async () => {
      await oracle.connect(subscriber).subscribe();
      expect(await oracle.getSubscriberCount()).to.be.greaterThan(0n);
    });

    it("unsubscribe removes authorization", async () => {
      await oracle.connect(subscriber).subscribe();
      await oracle.connect(subscriber).unsubscribe();
      await expect(
        oracle.connect(subscriber).updateSectorThreat("water", 5000, 3, "ddos")
      ).to.be.revertedWith("Oracle: Not authorized");
    });
  });

  describe("resetSector", () => {
    it("resets sector to zero threat", async () => {
      await oracle.updateSectorThreat("airport", 8000, 5, "ddos");
      await oracle.resetSector("airport");
      const [safe] = await oracle.isSectorSafe("airport");
      expect(safe).to.be.true;
    });
  });
});
