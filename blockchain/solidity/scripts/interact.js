/**
 * ImmunoGrid — Contract Interaction Script
 * Demo: record attacks, spawn honeypots, check morphogenesis
 *
 * Run after deploying:
 *   npx hardhat run scripts/interact.js --network hardhat
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function loadDeployment(networkName) {
  const p = path.join(__dirname, `../deployments/${networkName}.json`);
  if (!fs.existsSync(p)) {
    throw new Error(`No deployment found for ${networkName}. Run deploy.js first.`);
  }
  return JSON.parse(fs.readFileSync(p));
}

async function main() {
  const [signer] = await ethers.getSigners();
  const network  = await ethers.provider.getNetwork();

  console.log("\n╔══════════════════════════════════════════════╗");
  console.log("║  ImmunoGrid — Contract Interaction Demo     ║");
  console.log("╚══════════════════════════════════════════════╝\n");

  let deployment;
  try {
    deployment = await loadDeployment(network.name);
  } catch {
    // For hardhat in-memory, redeploy inline
    console.log("Deploying contracts for demo...\n");
    const IG   = await ethers.getContractFactory("ImmunoGrid");
    const KR   = await ethers.getContractFactory("ImmunoGridKeyRegistry");
    const FL   = await ethers.getContractFactory("ImmunoGridFL");
    const HP   = await ethers.getContractFactory("ImmunoGridHoneypot");
    const AC   = await ethers.getContractFactory("ImmunoGridAccess");

    const ig = await IG.deploy(); await ig.waitForDeployment();
    const kr = await KR.deploy(); await kr.waitForDeployment();
    const fl = await FL.deploy(); await fl.waitForDeployment();
    const hp = await HP.deploy(); await hp.waitForDeployment();
    const ac = await AC.deploy(); await ac.waitForDeployment();

    deployment = { contracts: {
      ImmunoGrid: await ig.getAddress(),
      ImmunoGridKeyRegistry: await kr.getAddress(),
      ImmunoGridFL: await fl.getAddress(),
      ImmunoGridHoneypot: await hp.getAddress(),
      ImmunoGridAccess: await ac.getAddress(),
    }};
    console.log("✅ Contracts deployed\n");
  }

  // Load contract instances
  const ig = await ethers.getContractAt("ImmunoGrid", deployment.contracts.ImmunoGrid);
  const kr = await ethers.getContractAt("ImmunoGridKeyRegistry", deployment.contracts.ImmunoGridKeyRegistry);
  const fl = await ethers.getContractAt("ImmunoGridFL", deployment.contracts.ImmunoGridFL);
  const hp = await ethers.getContractAt("ImmunoGridHoneypot", deployment.contracts.ImmunoGridHoneypot);
  const ac = await ethers.getContractAt("ImmunoGridAccess", deployment.contracts.ImmunoGridAccess);

  // ── Demo 1: Record Attacks ─────────────────────────────────────────────────
  console.log("═══ Demo 1: Recording Attack Events ═══");

  const attacks = [
    { type: "spoofing",       device: "traffic-sensor-001", sector: "traffic",  sev: 2 },
    { type: "ddos",           device: "hospital-device-042",sector: "hospital", sev: 3 },
    { type: "data_poisoning", device: "water-monitor-018",  sector: "water",    sev: 2 },
    { type: "replay_attack",  device: "power-sensor-007",   sector: "power",    sev: 1 },
    { type: "ransomware",     device: "govt-node-003",       sector: "government",sev: 3 },
  ];

  for (const atk of attacks) {
    const tx = await ig.recordAttack(
      atk.type, atk.device, atk.sector, atk.sev, "quantum_fingerprint", "raw_data"
    );
    await tx.wait();
    const isolated = await ig.isSectorIsolated(atk.sector);
    const quarantined = await ig.isDeviceQuarantined(atk.device);
    console.log(`  ⚔️  ${atk.type.padEnd(18)} → sector=${atk.sector.padEnd(12)} isolated=${isolated} quarantined=${quarantined}`);
  }

  // ── Demo 2: Check Morphogenesis ────────────────────────────────────────────
  console.log("\n═══ Demo 2: Network Morphogenesis State ═══");
  const [totalAttacks, totalMorph, honeypots, fpBps, version] = await ig.getStats();
  console.log(`  Total Attacks:      ${totalAttacks}`);
  console.log(`  Morphogenesis:      ${totalMorph}`);
  console.log(`  Active Honeypots:   ${honeypots}`);
  console.log(`  FP Sensitivity:     ${(Number(fpBps) / 100).toFixed(2)}%`);
  console.log(`  Chain Version:      ${version}`);

  // ── Demo 3: Pattern Recognition ───────────────────────────────────────────
  console.log("\n═══ Demo 3: Immune Memory Pattern Recognition ═══");
  const spoofTrafficCount = await ig.isPatternKnown("spoofing", "traffic");
  const ddosCount         = await ig.isPatternKnown("ddos", "hospital");
  const unknownCount      = await ig.isPatternKnown("quantum_breach", "traffic");
  console.log(`  spoofing:traffic    → ${spoofTrafficCount} (known: ${spoofTrafficCount > 0})`);
  console.log(`  ddos:hospital       → ${ddosCount} (known: ${ddosCount > 0})`);
  console.log(`  quantum_breach:*    → ${unknownCount} (known: ${unknownCount > 0})`);

  // ── Demo 4: PQC Key Registry ──────────────────────────────────────────────
  console.log("\n═══ Demo 4: PQC Key Registry ═══");
  const deviceIds = ["traffic-001", "hospital-042", "water-018"];
  for (const id of deviceIds) {
    const kemHash = ethers.keccak256(ethers.toUtf8Bytes(`kyber-${id}`));
    const sigHash = ethers.keccak256(ethers.toUtf8Bytes(`dilithium-${id}`));
    await (await kr.registerDevice(id, kemHash, sigHash)).wait();
  }
  console.log(`  Registered ${deviceIds.length} devices`);

  const [valid, reason] = await kr.verifyKey(
    "traffic-001",
    ethers.keccak256(ethers.toUtf8Bytes("kyber-traffic-001")),
    ethers.keccak256(ethers.toUtf8Bytes("dilithium-traffic-001"))
  );
  console.log(`  Verify traffic-001: valid=${valid} reason="${reason}"`);

  const [badValid, badReason] = await kr.verifyKey(
    "traffic-001",
    ethers.keccak256(ethers.toUtf8Bytes("wrong-key")),
    ethers.keccak256(ethers.toUtf8Bytes("dilithium-traffic-001"))
  );
  console.log(`  Impostor check:     valid=${badValid} reason="${badReason}"`);

  // ── Demo 5: FL Model Registry ─────────────────────────────────────────────
  console.log("\n═══ Demo 5: Federated Learning Model Registry ═══");
  for (let r = 1; r <= 3; r++) {
    const modelHash = ethers.keccak256(ethers.toUtf8Bytes(`model-round-${r}`));
    const gradHash  = ethers.keccak256(ethers.toUtf8Bytes(`grads-round-${r}`));
    const accuracy  = 9500 + r * 70;
    await (await fl.commitModelVersion(modelHash, gradHash, accuracy, 500, 490, 1200)).wait();
    const version = await fl.getModelVersion(r);
    console.log(`  Round ${r}: accuracy=${(Number(version.accuracy)/100).toFixed(2)}%  participants=${version.participants}`);
  }

  const [acc, round] = await fl.getLatestAccuracy();
  console.log(`  Latest accuracy: ${(Number(acc)/100).toFixed(2)}% (round ${round})`);

  // ── Demo 6: Honeypot Intelligence ─────────────────────────────────────────
  console.log("\n═══ Demo 6: Honeypot Intelligence Registry ═══");
  const attackers = ["atk-node-001", "atk-node-002", "atk-node-001"]; // 001 appears twice
  for (const atk of attackers) {
    const attackerHash = ethers.keccak256(ethers.toUtf8Bytes(atk));
    const behaviorHash = ethers.keccak256(ethers.toUtf8Bytes(`behavior-${atk}-${Date.now()}`));
    await (await hp.fileReport(attackerHash, "spoofing", "traffic", 5, behaviorHash, 12)).wait();
  }

  const [known001, attempts001] = await hp.isKnownAttacker(
    ethers.keccak256(ethers.toUtf8Bytes("atk-node-001"))
  );
  console.log(`  Attacker atk-node-001: known=${known001} total_attempts=${attempts001}`);

  const [hpReports, hpSamples, hpAttackers] = await hp.getStats();
  console.log(`  Total reports=${hpReports} AI_samples=${hpSamples} unique_attackers=${hpAttackers}`);

  // ── Demo 7: RBAC Access Control ───────────────────────────────────────────
  console.log("\n═══ Demo 7: Role-Based Access Control ═══");
  const [signers] = [await ethers.getSigners()];
  console.log(`  Owner canRecordAttack:     ${await ac.canRecordAttack(signer.address)}`);
  console.log(`  Owner canTriggerMorphogenesis: ${await ac.canTriggerMorphogenesis(signer.address)}`);
  console.log(`  Owner canReadSector traffic: ${await ac.canReadSector(signer.address, "traffic")}`);
  console.log(`  Owner canReadSector hospital: ${await ac.canReadSector(signer.address, "hospital")}`);

  console.log("\n╔══════════════════════════════════════════════╗");
  console.log("║  ALL DEMOS COMPLETE — Blockchain working! ✅ ║");
  console.log("╚══════════════════════════════════════════════╝\n");
}

main().catch((err) => { console.error(err); process.exitCode = 1; });
