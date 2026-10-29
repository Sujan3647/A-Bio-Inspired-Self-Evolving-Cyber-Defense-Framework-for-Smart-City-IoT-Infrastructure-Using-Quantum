/**
 * ImmunoGrid — Post-Deploy Contract Verification
 * Verifies all deployed contracts are working correctly after deployment.
 *
 * Run:
 *   npx hardhat run scripts/verify.js --network hardhat
 *   npx hardhat run scripts/verify.js --network sepolia
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

function ok(msg)   { console.log(`  ✅ ${msg}`); }
function fail(msg) { console.log(`  ❌ ${msg}`); process.exitCode = 1; }
function section(title) { console.log(`\n── ${title} ${"─".repeat(45 - title.length)}`); }

async function loadContracts(networkName) {
  const p = path.join(__dirname, `../deployments/${networkName}.json`);
  if (!fs.existsSync(p)) throw new Error(`No deployment for ${networkName}`);
  const deployment = JSON.parse(fs.readFileSync(p));
  const addrs = deployment.contracts;
  return {
    ig:     await ethers.getContractAt("ImmunoGrid",             addrs.ImmunoGrid),
    kr:     await ethers.getContractAt("ImmunoGridKeyRegistry",  addrs.ImmunoGridKeyRegistry),
    fl:     await ethers.getContractAt("ImmunoGridFL",           addrs.ImmunoGridFL),
    hp:     await ethers.getContractAt("ImmunoGridHoneypot",     addrs.ImmunoGridHoneypot),
    ac:     await ethers.getContractAt("ImmunoGridAccess",       addrs.ImmunoGridAccess),
    oracle: await ethers.getContractAt("ImmunoGridOracle",       addrs.ImmunoGridOracle),
  };
}

async function deployFresh() {
  const names = ["ImmunoGrid","ImmunoGridKeyRegistry","ImmunoGridFL","ImmunoGridHoneypot","ImmunoGridAccess"];
  const contracts = {};
  for (const name of names) {
    const F = await ethers.getContractFactory(name);
    const c = await F.deploy();
    await c.waitForDeployment();
    contracts[name] = c;
  }
  // Oracle needs ImmunoGrid address
  const OF = await ethers.getContractFactory("ImmunoGridOracle");
  contracts.ImmunoGridOracle = await OF.deploy(await contracts.ImmunoGrid.getAddress());
  await contracts.ImmunoGridOracle.waitForDeployment();

  return {
    ig:     contracts.ImmunoGrid,
    kr:     contracts.ImmunoGridKeyRegistry,
    fl:     contracts.ImmunoGridFL,
    hp:     contracts.ImmunoGridHoneypot,
    ac:     contracts.ImmunoGridAccess,
    oracle: contracts.ImmunoGridOracle,
  };
}

async function main() {
  const [owner] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();

  console.log("\n╔══════════════════════════════════════════════╗");
  console.log("║   ImmunoGrid — Contract Verification        ║");
  console.log("╚══════════════════════════════════════════════╝");
  console.log(`Network:  ${network.name} (chainId: ${network.chainId})`);
  console.log(`Verifier: ${owner.address}\n`);

  let contracts;
  try {
    contracts = await loadContracts(network.name);
    console.log("Loaded existing deployment\n");
  } catch {
    console.log("No existing deployment — deploying fresh for verification...\n");
    contracts = await deployFresh();
  }

  const { ig, kr, fl, hp, ac, oracle } = contracts;
  let passed = 0, failed = 0;

  function check(name, condition) {
    if (condition) { ok(name); passed++; }
    else           { fail(name); failed++; }
  }

  // ── ImmunoGrid ────────────────────────────────────────────────────────────────
  section("ImmunoGrid — Attack Registry");

  check("owner set", (await ig.owner()) === owner.address);
  check("total attacks starts at 0", (await ig.totalAttacks()) === 0n);
  check("chain version is 1", (await ig.chainVersion()) === 1n);

  // Record a test attack
  const tx = await ig.recordAttack("spoofing","test-dev","traffic",2,"quantum","raw");
  await tx.wait();
  check("record attack increments counter", (await ig.totalAttacks()) === 1n);
  check("morphogenesis triggered",          (await ig.getTopology()).morphogenesisCount > 0n);
  check("honeypots increased",              (await ig.getTopology()).honeypotCount > 5n);
  check("fp sensitivity decreased",         (await ig.getTopology()).fpSensitivityBps < 9200n);

  // Pattern recognition
  await (await ig.recordAttack("spoofing","dev2","traffic",1,"quantum","raw")).wait();
  check("pattern count is 2", (await ig.isPatternKnown("spoofing","traffic")) === 2n);

  // Stats
  const [attacks, morph, honeypots, fp, ver] = await ig.getStats();
  check("getStats: attacks=2",       attacks === 2n);
  check("getStats: morphogenesis>0", morph > 0n);
  check("getStats: honeypots>5",     honeypots > 5n);
  check("getStats: version=1",       ver === 1n);

  // Sector isolation
  await (await ig.recordAttack("ddos","dev3","hospital",3,"ai","raw")).wait();
  check("hospital sector isolated after critical DDoS", await ig.isSectorIsolated("hospital"));

  // Device quarantine
  check("dev2 is quarantined", await ig.isDeviceQuarantined("dev2"));

  // ── Key Registry ──────────────────────────────────────────────────────────────
  section("ImmunoGridKeyRegistry — PQC Keys");

  const kemHash = ethers.keccak256(ethers.toUtf8Bytes("kyber-test-001"));
  const sigHash = ethers.keccak256(ethers.toUtf8Bytes("dilithium-test-001"));
  await (await kr.registerDevice("verify-device", kemHash, sigHash)).wait();

  const [valid, reason] = await kr.verifyKey("verify-device", kemHash, sigHash);
  check("verify matching keys → valid",  valid === true);
  check("verify reason is 'Valid'",      reason === "Valid");

  const [inv, invReason] = await kr.verifyKey("verify-device", ethers.keccak256(ethers.toUtf8Bytes("wrong")), sigHash);
  check("verify wrong key → invalid",   inv === false);
  check("reason: KEM key mismatch",     invReason.includes("mismatch"));

  const [unk] = await kr.verifyKey("not-registered", kemHash, sigHash);
  check("unknown device → invalid",     unk === false);

  await (await kr.revokeKey("verify-device","test")).wait();
  const [rev] = await kr.verifyKey("verify-device", kemHash, sigHash);
  check("revoked device → invalid",     rev === false);

  // Bulk register
  const ids = ["bulk-1","bulk-2","bulk-3"];
  const hashes = ids.map(id => ethers.keccak256(ethers.toUtf8Bytes(id)));
  await (await kr.bulkRegister(ids, hashes, hashes)).wait();
  check("bulk register 3 devices",      (await kr.getDeviceCount()) >= 3n);

  // ── FL Registry ───────────────────────────────────────────────────────────────
  section("ImmunoGridFL — Model Provenance");

  const mh = ethers.keccak256(ethers.toUtf8Bytes("model-verify-1"));
  await (await fl.commitModelVersion(mh, ethers.keccak256(ethers.toUtf8Bytes("g1")), 9720, 500, 492, 1200)).wait();

  check("round increments to 1",        (await fl.currentRound()) === 1n);
  check("model is verifiable",          await fl.verifyModel(mh));
  check("unknown model is not verified",!(await fl.verifyModel(ethers.keccak256(ethers.toUtf8Bytes("unknown")))));

  const [acc, round] = await fl.getLatestAccuracy();
  check("latest accuracy=9720",         acc === 9720n);
  check("latest round=1",               round === 1n);

  const v = await fl.getModelVersion(1);
  check("model version stored",         v.accuracy === 9720n && v.participants === 492n);

  // Poisoning detection
  await (await fl.flagPoisoning(1,"malicious-device")).wait();
  check("poisoning flagged on round 1", (await fl.getModelVersion(1)).poisoningDetected);

  // ── Honeypot Registry ─────────────────────────────────────────────────────────
  section("ImmunoGridHoneypot — Threat Intelligence");

  const aHash = ethers.keccak256(ethers.toUtf8Bytes("threat-actor-001"));
  const bHash = ethers.keccak256(ethers.toUtf8Bytes("behavior-sig-001"));
  await (await hp.fileReport(aHash,"spoofing","traffic",5,bHash,12)).wait();

  check("report filed",                 (await hp.totalReports()) === 1n);
  check("attacker profiled",            (await hp.totalAttackersProfiled()) === 1n);

  const [known, attempts] = await hp.isKnownAttacker(aHash);
  check("attacker is known",            known);
  check("attempt count=5",              attempts === 5n);

  // Repeat report same attacker
  const bHash2 = ethers.keccak256(ethers.toUtf8Bytes("behavior-sig-002"));
  await (await hp.fileReport(aHash,"ddos","hospital",8,bHash2,20)).wait();
  const [,newAttempts] = await hp.isKnownAttacker(aHash);
  check("attempts accumulated=13",      newAttempts === 13n);
  check("AI samples accumulated=32",    (await hp.totalAiSamples()) === 32n);

  // ── Access Control ────────────────────────────────────────────────────────────
  section("ImmunoGridAccess — RBAC");

  const SUPER_ADMIN = ethers.keccak256(ethers.toUtf8Bytes("SUPER_ADMIN"));
  check("owner has SUPER_ADMIN",        await ac.hasRole(SUPER_ADMIN, owner.address));
  check("owner can record attacks",     await ac.canRecordAttack(owner.address));
  check("owner can trigger morphogenesis", await ac.canTriggerMorphogenesis(owner.address));
  check("owner can read all sectors",   await ac.canReadSector(owner.address, "hospital"));

  const [, roleName, ministry, canRec, canMorph] = await ac.getUserInfo(owner.address);
  check("role name correct",            roleName === "Super Admin");
  check("ministry set",                 ministry === "National Cybersecurity Authority");

  // ── Oracle ────────────────────────────────────────────────────────────────────
  section("ImmunoGridOracle — Threat Feed");

  await oracle.subscribe();
  check("owner subscribed",             await oracle.subscribers(owner.address));
  check("initial global threat is 0",   (await oracle.globalThreatScore()) === 0n);

  await (await oracle.updateSectorThreat("traffic",5000,3,"spoofing")).wait();
  const [safe, , score] = await oracle.isSectorSafe("traffic");
  check("traffic not safe at score 5000", !safe);
  check("traffic score=5000",            score === 5000n);

  await (await oracle.updateDeviceTrust("trusted-dev",9700,9850)).wait();
  const [trusted] = await oracle.isDeviceTrusted("trusted-dev");
  check("device trust=9700 is trusted", trusted);

  await (await oracle.updateDeviceTrust("untrusted-dev",7000,7500)).wait();
  const [untrusted] = await oracle.isDeviceTrusted("untrusted-dev");
  check("device trust=7000 not trusted", !untrusted);

  const [sectors, levels] = await oracle.getAllSectorThreats();
  check("all 8 sectors returned",       sectors.length === 8);

  await (await oracle.resetSector("traffic")).wait();
  const [safeAfterReset] = await oracle.isSectorSafe("traffic");
  check("sector safe after reset",      safeAfterReset);

  // ── Final Report ──────────────────────────────────────────────────────────────
  console.log("\n╔══════════════════════════════════════════════╗");
  console.log(`║  Verification: ${passed} passed, ${failed} failed           ║`);
  console.log("╚══════════════════════════════════════════════╝\n");

  if (failed === 0) {
    console.log("✅ ALL CONTRACTS VERIFIED — Ready for production\n");
  } else {
    console.log(`❌ ${failed} check(s) failed — Review before deploying to mainnet\n`);
    process.exit(1);
  }
}

main().catch(err => { console.error(err); process.exit(1); });
