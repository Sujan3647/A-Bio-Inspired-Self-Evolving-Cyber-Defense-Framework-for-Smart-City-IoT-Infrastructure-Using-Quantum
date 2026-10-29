/**
 * ImmunoGrid — Seed Initial Blockchain Data
 * Populates deployed contracts with realistic demo data.
 *
 * Run after deploy:
 *   npx hardhat run scripts/seed_data.js --network hardhat
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function loadOrDeploy(name, ...args) {
  const Factory = await ethers.getContractFactory(name);
  const contract = await Factory.deploy(...args);
  await contract.waitForDeployment();
  return contract;
}

async function main() {
  const [owner] = await ethers.getSigners();
  console.log("\n🌱 Seeding ImmunoGrid blockchain data...\n");

  // Deploy all contracts
  const ig = await loadOrDeploy("ImmunoGrid");
  const kr = await loadOrDeploy("ImmunoGridKeyRegistry");
  const fl = await loadOrDeploy("ImmunoGridFL");
  const hp = await loadOrDeploy("ImmunoGridHoneypot");
  const ac = await loadOrDeploy("ImmunoGridAccess");
  const oracle = await loadOrDeploy("ImmunoGridOracle", await ig.getAddress());

  console.log("✅ All contracts deployed\n");

  // ── Seed: Device Keys ─────────────────────────────────────────────────────
  console.log("📡 Registering IoT device keys...");
  const devices = [
    "traffic-sensor-001", "traffic-sensor-002", "traffic-sensor-003",
    "hospital-device-001", "hospital-device-002",
    "water-monitor-001",  "water-monitor-002",
    "power-sensor-001",   "power-sensor-002",
    "metro-sensor-001",
  ];
  const kemHashes = devices.map(d => ethers.keccak256(ethers.toUtf8Bytes(`kyber-${d}`)));
  const sigHashes = devices.map(d => ethers.keccak256(ethers.toUtf8Bytes(`dilithium-${d}`)));
  await (await kr.bulkRegister(devices, kemHashes, sigHashes)).wait();
  console.log(`  Registered ${devices.length} devices\n`);

  // ── Seed: Attack Records ──────────────────────────────────────────────────
  console.log("⚔️  Recording attack history...");
  const attacks = [
    { type: "spoofing",       device: "traffic-sensor-001", sector: "traffic",   sev: 2 },
    { type: "ddos",           device: "hospital-device-001",sector: "hospital",  sev: 3 },
    { type: "data_poisoning", device: "water-monitor-001",  sector: "water",     sev: 1 },
    { type: "replay_attack",  device: "power-sensor-001",   sector: "power",     sev: 2 },
    { type: "spoofing",       device: "traffic-sensor-002", sector: "traffic",   sev: 2 },
    { type: "ransomware",     device: "hospital-device-002",sector: "hospital",  sev: 3 },
    { type: "mitm",           device: "metro-sensor-001",   sector: "metro",     sev: 2 },
    { type: "data_poisoning", device: "water-monitor-002",  sector: "water",     sev: 2 },
  ];
  for (const a of attacks) {
    await (await ig.recordAttack(a.type, a.device, a.sector, a.sev, "quantum_fingerprint", "raw")).wait();
    process.stdout.write(".");
  }
  console.log(`\n  Recorded ${attacks.length} attacks\n`);

  // ── Seed: FL Model Versions ───────────────────────────────────────────────
  console.log("🤖 Committing FL model versions...");
  for (let r = 1; r <= 10; r++) {
    const acc = Math.floor(9300 + r * 65 + Math.random() * 30);
    const loss = Math.floor(1500 - r * 110);
    await (await fl.commitModelVersion(
      ethers.keccak256(ethers.toUtf8Bytes(`model-round-${r}-${Date.now()}`)),
      ethers.keccak256(ethers.toUtf8Bytes(`grads-${r}`)),
      acc, loss, 490 + r, 1200
    )).wait();
    process.stdout.write(".");
  }
  console.log(`\n  10 FL rounds committed\n`);

  // ── Seed: Honeypot Reports ────────────────────────────────────────────────
  console.log("🍯 Filing honeypot intelligence reports...");
  const honeypotAttackers = [
    { id: "threat-actor-001", type: "spoofing",       sector: "traffic",  ints: 8 },
    { id: "threat-actor-002", type: "ddos",           sector: "hospital", ints: 15 },
    { id: "threat-actor-003", type: "data_poisoning", sector: "water",    ints: 5 },
    { id: "threat-actor-001", type: "spoofing",       sector: "power",    ints: 3 },  // repeat
    { id: "threat-actor-004", type: "ransomware",     sector: "hospital", ints: 12 },
  ];
  for (const h of honeypotAttackers) {
    const attackerHash = ethers.keccak256(ethers.toUtf8Bytes(h.id));
    const behaviorHash = ethers.keccak256(ethers.toUtf8Bytes(`behavior-${h.id}-${Date.now()}`));
    await (await hp.fileReport(attackerHash, h.type, h.sector, h.ints, behaviorHash, h.ints * 2)).wait();
    process.stdout.write(".");
  }
  console.log(`\n  ${honeypotAttackers.length} honeypot reports filed\n`);

  // ── Seed: Oracle Threat Levels ────────────────────────────────────────────
  console.log("📡 Setting oracle threat levels...");
  await oracle.subscribe();
  const threatLevels = [
    { sector: "traffic",      score: 1500, attacks: 2 },
    { sector: "hospital",     score: 6800, attacks: 5 },  // HIGH
    { sector: "water",        score: 800,  attacks: 1 },
    { sector: "power",        score: 3200, attacks: 2 },
    { sector: "surveillance", score: 200,  attacks: 0 },
    { sector: "metro",        score: 2100, attacks: 1 },
  ];
  for (const t of threatLevels) {
    await (await oracle.updateSectorThreat(t.sector, t.score, t.attacks, "spoofing")).wait();
    process.stdout.write(".");
  }
  console.log(`\n  Threat oracle updated\n`);

  // ── Seed: RBAC Roles ──────────────────────────────────────────────────────
  console.log("👥 Setting up RBAC roles...");
  const ROLES = {
    NATIONAL_SECURITY_OFFICER: ethers.keccak256(ethers.toUtf8Bytes("NATIONAL_SECURITY_OFFICER")),
    TRAFFIC_MINISTRY:          ethers.keccak256(ethers.toUtf8Bytes("TRAFFIC_MINISTRY")),
    HEALTH_MINISTRY:           ethers.keccak256(ethers.toUtf8Bytes("HEALTH_MINISTRY")),
    BLOCKCHAIN_AUDITOR:        ethers.keccak256(ethers.toUtf8Bytes("BLOCKCHAIN_AUDITOR")),
  };
  // In production: grant to actual ministry wallet addresses
  // For demo: grant to derived addresses
  const signers = await ethers.getSigners();
  if (signers.length >= 4) {
    await (await ac.grantRole(ROLES.NATIONAL_SECURITY_OFFICER, signers[1].address, "Ministry of Interior")).wait();
    await (await ac.grantRole(ROLES.TRAFFIC_MINISTRY,          signers[2].address, "Ministry of Transport")).wait();
    await (await ac.grantRole(ROLES.HEALTH_MINISTRY,           signers[3].address, "Ministry of Health")).wait();
    console.log("  3 government roles assigned\n");
  }

  // ── Summary ───────────────────────────────────────────────────────────────
  const [totalAttacks, totalMorph, honeypots, fpBps] = await ig.getStats();
  const [currentRound, totalImag] = await fl.getStats();
  const [totalReports, totalSamples] = await hp.getStats();
  const [globalScore, globalLevel]  = await oracle.getGlobalThreat();

  console.log("╔══════════════════════════════════════════╗");
  console.log("║      Seed Data Summary                   ║");
  console.log("╚══════════════════════════════════════════╝");
  console.log(`  Attack records:       ${totalAttacks}`);
  console.log(`  Morphogenesis events: ${totalMorph}`);
  console.log(`  Active honeypots:     ${honeypots}`);
  console.log(`  FP sensitivity:       ${(Number(fpBps)/100).toFixed(2)}%`);
  console.log(`  FL rounds committed:  ${currentRound}`);
  console.log(`  Total imaginations:   ${totalImag}`);
  console.log(`  Honeypot reports:     ${totalReports}`);
  console.log(`  AI samples generated: ${totalSamples}`);
  console.log(`  Global threat score:  ${globalScore} (level ${globalLevel})`);
  console.log("\n✅ Seed data complete!\n");
}

main().catch((err) => { console.error(err); process.exitCode = 1; });
