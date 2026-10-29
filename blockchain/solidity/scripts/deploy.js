/**
 * ImmunoGrid — Solidity Contract Deployment Script
 *
 * Deploys all 4 contracts in order:
 *   1. ImmunoGrid          — Main attack registry + morphogenesis
 *   2. ImmunoGridKeyRegistry — PQC key management
 *   3. ImmunoGridFL        — Federated learning provenance
 *   4. ImmunoGridHoneypot  — Honeypot intelligence registry
 *
 * Usage:
 *   npx hardhat run scripts/deploy.js --network hardhat     (local)
 *   npx hardhat run scripts/deploy.js --network sepolia     (testnet)
 *   npx hardhat run scripts/deploy.js --network besu        (private)
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();

  console.log("\n╔═══════════════════════════════════════════╗");
  console.log("║   ImmunoGrid — Contract Deployment        ║");
  console.log("╚═══════════════════════════════════════════╝\n");
  console.log(`Network:  ${network.name} (chainId: ${network.chainId})`);
  console.log(`Deployer: ${deployer.address}`);
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`Balance:  ${ethers.formatEther(balance)} ETH\n`);

  const deployed = {};

  // ── 1. ImmunoGrid Main Contract ─────────────────────────────────────────────
  console.log("1. Deploying ImmunoGrid (Attack Registry + Morphogenesis)...");
  const ImmunoGrid = await ethers.getContractFactory("ImmunoGrid");
  const immunoGrid = await ImmunoGrid.deploy();
  await immunoGrid.waitForDeployment();
  deployed.ImmunoGrid = await immunoGrid.getAddress();
  console.log(`   ✅ ImmunoGrid deployed at: ${deployed.ImmunoGrid}`);

  // ── 2. Key Registry ──────────────────────────────────────────────────────────
  console.log("2. Deploying ImmunoGridKeyRegistry (PQC Key Management)...");
  const KeyRegistry = await ethers.getContractFactory("ImmunoGridKeyRegistry");
  const keyRegistry = await KeyRegistry.deploy();
  await keyRegistry.waitForDeployment();
  deployed.ImmunoGridKeyRegistry = await keyRegistry.getAddress();
  console.log(`   ✅ KeyRegistry deployed at: ${deployed.ImmunoGridKeyRegistry}`);

  // ── 3. FL Registry ───────────────────────────────────────────────────────────
  console.log("3. Deploying ImmunoGridFL (FL Model Provenance)...");
  const FLRegistry = await ethers.getContractFactory("ImmunoGridFL");
  const flRegistry = await FLRegistry.deploy();
  await flRegistry.waitForDeployment();
  deployed.ImmunoGridFL = await flRegistry.getAddress();
  console.log(`   ✅ FL Registry deployed at: ${deployed.ImmunoGridFL}`);

  // ── 4. Honeypot Registry ─────────────────────────────────────────────────────
  console.log("4. Deploying ImmunoGridHoneypot (Threat Intelligence)...");
  const HoneypotRegistry = await ethers.getContractFactory("ImmunoGridHoneypot");
  const honeypotRegistry = await HoneypotRegistry.deploy();
  await honeypotRegistry.waitForDeployment();
  deployed.ImmunoGridHoneypot = await honeypotRegistry.getAddress();
  console.log(`   ✅ Honeypot Registry deployed at: ${deployed.ImmunoGridHoneypot}`);

  // ── Save deployment addresses ─────────────────────────────────────────────────
  const deploymentInfo = {
    network:   network.name,
    chainId:   network.chainId.toString(),
    deployer:  deployer.address,
    timestamp: new Date().toISOString(),
    contracts: deployed,
  };

  const outputPath = path.join(__dirname, `../deployments/${network.name}.json`);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(deploymentInfo, null, 2));

  console.log("\n╔═══════════════════════════════════════════╗");
  console.log("║   ALL CONTRACTS DEPLOYED SUCCESSFULLY     ║");
  console.log("╚═══════════════════════════════════════════╝\n");
  console.log("Contract Addresses:");
  Object.entries(deployed).forEach(([name, addr]) => {
    console.log(`  ${name.padEnd(28)} ${addr}`);
  });
  console.log(`\nAddresses saved to: ${outputPath}\n`);

  // ── Verify on Etherscan (if not local) ───────────────────────────────────────
  if (network.name !== "hardhat" && network.name !== "ganache") {
    console.log("Waiting 30s before Etherscan verification...");
    await new Promise(r => setTimeout(r, 30000));
    for (const [name, addr] of Object.entries(deployed)) {
      try {
        await hre.run("verify:verify", { address: addr, constructorArguments: [] });
        console.log(`✅ ${name} verified on Etherscan`);
      } catch (e) {
        console.log(`⚠️  ${name} verification: ${e.message}`);
      }
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
