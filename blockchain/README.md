# ImmunoGrid — Blockchain Layer

> **Morphogenetic Blockchain** — Bio-Inspired Immune Memory for Smart City Cyber Defense

---

## Overview

The ImmunoGrid blockchain layer consists of **4 implementations** spanning 3 platforms:

| Layer | Technology | Purpose |
|---|---|---|
| Python Immune Ledger | Pure Python + SHA-256 PoW | Fast local simulation, research demos |
| Python Smart Contract | Python simulation of Solidity | Testing morphogenesis logic locally |
| Solidity Contracts | Ethereum / Hyperledger Besu | Production blockchain deployment |
| Hyperledger Fabric | Go chaincode | Enterprise permissioned blockchain |

---

## Architecture

```
Smart City Attack Detected
          ↓
    PBFT Consensus (4 nodes)
          ↓ (2f+1 agreement)
  ┌───────────────────────────┐
  │   ImmunoGrid.sol          │  ← Main attack registry
  │   ImmunoGridKeyRegistry   │  ← PQC device keys
  │   ImmunoGridFL.sol        │  ← FL model provenance
  │   ImmunoGridHoneypot.sol  │  ← Threat intelligence
  │   ImmunoGridAccess.sol    │  ← RBAC (13 roles)
  │   ImmunoGridOracle.sol    │  ← Real-time threat feed
  └───────────────────────────┘
          ↓
  Network Morphogenesis Triggered
  (topology reshapes via smart contract)
```

---

## Folder Structure

```
blockchain/
├── immune_ledger.py        Python blockchain (PoW, morphogenesis)
├── smart_contract.py       Python simulation of Solidity logic
├── consensus.py            PBFT Byzantine fault-tolerant consensus
├── web3_bridge.py          Python→Solidity bridge (Web3.py)
├── test_blockchain_complete.py  33 tests for all Python layers
│
├── solidity/               Ethereum / Hyperledger Besu
│   ├── ImmunoGrid.sol         Main attack registry + morphogenesis
│   ├── ImmunoGridKey.sol      PQC key management (Kyber + Dilithium)
│   ├── ImmunoGridFL.sol       Federated learning model provenance
│   ├── ImmunoGridHoneypot.sol Honeypot threat intelligence
│   ├── ImmunoGridAccess.sol   13-role government RBAC
│   ├── ImmunoGridOracle.sol   Real-time threat oracle
│   ├── hardhat.config.js      Hardhat configuration
│   ├── package.json
│   ├── scripts/
│   │   ├── deploy.js          Deploy all 6 contracts
│   │   ├── verify.js          Post-deploy verification (50+ checks)
│   │   ├── seed_data.js       Populate with demo data
│   │   └── interact.js        Interactive demo
│   └── test/
│       ├── ImmunoGrid.test.js         Main + Key + FL + Honeypot tests
│       ├── ImmunoGridAccess.test.js   RBAC tests
│       └── ImmunoGridFL.test.js       FL + Honeypot + Oracle tests
│
├── chaincode/              Hyperledger Fabric (Go)
│   ├── immunogrid.go       Full chaincode implementation
│   ├── immunogrid_test.go  Go unit tests
│   └── go.mod              Go module definition
│
└── fabric_network/         Hyperledger Fabric network
    ├── crypto-config.yaml  Network participants
    ├── configtx.yaml       Channel configuration
    ├── docker-compose.yml  4-peer network containers
    └── network.sh          Network management script
```

---

## Quick Start

### Run Python Tests (no dependencies needed)

```bash
cd blockchain
python test_blockchain_complete.py
# Expected: 33/33 PASS
```

### Deploy Solidity Contracts (local Hardhat node)

```bash
cd blockchain/solidity
npm install
npx hardhat compile
npx hardhat test                    # Run all JS unit tests
npx hardhat node                    # Start local blockchain
# In new terminal:
npx hardhat run scripts/deploy.js   --network hardhat
npx hardhat run scripts/seed_data.js --network hardhat
npx hardhat run scripts/verify.js   --network hardhat
npx hardhat run scripts/interact.js --network hardhat
```

### Deploy to Ethereum Testnet (Sepolia)

```bash
# Set env vars
export PRIVATE_KEY=your_wallet_private_key
export SEPOLIA_RPC_URL=https://rpc.sepolia.org
export ETHERSCAN_API_KEY=your_etherscan_key

npx hardhat run scripts/deploy.js --network sepolia
npx hardhat run scripts/verify.js --network sepolia
```

### Deploy to Hyperledger Besu (private network)

```bash
export BESU_RPC_URL=http://localhost:8545
export BESU_PRIVATE_KEY=your_besu_key

npx hardhat run scripts/deploy.js --network besu
```

### Run Go Chaincode Tests

```bash
cd blockchain/chaincode
go test ./... -v
```

### Start Hyperledger Fabric Network

```bash
cd blockchain/fabric_network
chmod +x network.sh
./network.sh up          # Start 4-peer network
./network.sh createChannel
./network.sh deployCC    # Deploy immunogrid chaincode
./network.sh status      # Check network health
./network.sh down        # Stop and cleanup
```

---

## Smart Contracts Reference

### ImmunoGrid.sol — Main Contract

```solidity
// Record an attack event (triggers morphogenesis automatically)
function recordAttack(
    string attackType,    // "spoofing"|"ddos"|"data_poisoning"|"replay_attack"|"ransomware"|"mitm"
    string deviceId,      // "traffic-sensor-001"
    string sector,        // "traffic"|"hospital"|"water"|"power"|"surveillance"|"metro"|"airport"|"government"
    uint8  severity,      // 0=LOW, 1=MEDIUM, 2=HIGH, 3=CRITICAL
    string detectedBy,    // "quantum_fingerprint"|"ai_brain"|"honeypot"
    string rawData        // raw attack data string
) returns (bytes32 recordId)

// Check if attack pattern is known (immune memory)
function isPatternKnown(string attackType, string sector) returns (uint256 count)

// Get current network topology (morphogenesis state)
function getTopology() returns (NetworkTopology memory)

// Check if sector is isolated
function isSectorIsolated(string sector) returns (bool)

// Restore isolated sector
function restoreSector(string sector)
```

### ImmunoGridKeyRegistry.sol — PQC Keys

```solidity
// Register IoT device with Kyber-512 + Dilithium-2 key hashes
function registerDevice(string deviceId, bytes32 kemKeyHash, bytes32 sigKeyHash)

// Verify device keys (returns false if wrong key = IMPOSTOR)
function verifyKey(string deviceId, bytes32 kemHash, bytes32 sigHash)
    returns (bool valid, string reason)

// Rotate device keys (scheduled or emergency)
function rotateKey(string deviceId, bytes32 newKemHash, bytes32 newSigHash, string reason)

// Emergency key revocation
function revokeKey(string deviceId, string reason)

// Bulk register devices
function bulkRegister(string[] deviceIds, bytes32[] kemHashes, bytes32[] sigHashes)
```

### ImmunoGridFL.sol — FL Model Provenance

```solidity
// Commit aggregated FL model version on-chain
function commitModelVersion(
    bytes32 modelHash, bytes32 gradientsHash,
    uint256 accuracyBps, uint256 lossBps,
    uint256 participants, uint256 imaginationsCount
) returns (uint256 roundNumber)

// Verify a model hash is committed (anti-poisoning)
function verifyModel(bytes32 modelHash) returns (bool)

// Flag Byzantine gradient poisoning
function flagPoisoning(uint256 roundNumber, string suspectDevice)
```

### ImmunoGridOracle.sol — Threat Feed

```solidity
// Update sector threat level (called by ImmunoGrid nodes)
function updateSectorThreat(string sector, uint256 score, uint256 attacks, string attackType)

// Check if sector is safe (score ≤ LOW)
function isSectorSafe(string sector) returns (bool safe, uint8 level, uint256 score)

// Check device trust from quantum fingerprint
function isDeviceTrusted(string deviceId) returns (bool trusted, uint256 score, uint256 fidelity)

// Get all 8 sectors at once
function getAllSectorThreats() returns (string[] sectors, uint8[] levels, uint256[] scores, bool[] underAttack)
```

---

## Morphogenesis Logic

When an attack is detected, smart contracts auto-execute:

| Attack Type | Severity | Actions |
|---|---|---|
| spoofing | LOW/MEDIUM | broadcast_alert + increase_fp_sensitivity + spawn_honeypots |
| spoofing | HIGH/CRITICAL | + quarantine_device |
| ddos | LOW/MEDIUM/HIGH | broadcast_alert + update_firewall + reroute_traffic |
| ddos | CRITICAL | + isolate_sector |
| data_poisoning | any | broadcast_alert + quarantine_device + update_firewall |
| replay_attack | any | broadcast_alert + quarantine_device + spawn_honeypots |
| ransomware | any | broadcast_alert + quarantine_device + spawn_honeypots |

---

## Test Results

```
Python blockchain tests:    33/33 PASS
Solidity unit tests:        ~60 tests (run: npx hardhat test)
Go chaincode tests:         ~20 tests (run: go test ./... -v)
```

---

## Novel Research Contributions

1. **Morphogenetic Blockchain** — blockchain that physically restructures network defense topology after each attack (first implementation)
2. **On-chain PQC Key Registry** — Kyber-512 + Dilithium-2 public key hashes stored immutably
3. **FL Model Provenance** — federated learning model versions committed on-chain with poisoning detection
4. **Honeypot Intelligence Registry** — attacker behavioral profiles stored permanently for global threat sharing
5. **Threat Oracle** — real-time threat scores exposed as on-chain oracle for external smart contracts
