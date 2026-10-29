"""
ImmunoGrid — Web3 Bridge
Connects the Python backend to the Solidity smart contracts
deployed on Ethereum / Hyperledger Besu.

Provides:
- record_attack()       → calls ImmunoGrid.recordAttack()
- register_device_key() → calls ImmunoGridKeyRegistry.registerDevice()
- commit_fl_model()     → calls ImmunoGridFL.commitModelVersion()
- file_honeypot_report()→ calls ImmunoGridHoneypot.fileReport()
- verify_device_key()   → calls ImmunoGridKeyRegistry.verifyKey()
- is_pattern_known()    → calls ImmunoGrid.isPatternKnown()
- get_contract_stats()  → calls all getStats()

Falls back to in-memory simulation if Web3 / contracts unavailable.
"""

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

# Try to import web3 — fall back to simulation
try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("web3_not_installed", mode="simulation",
                   note="pip install web3 for real contract interaction")


# ── ABI Fragments ─────────────────────────────────────────────────────────────
# Minimal ABI for the functions we use

IMMUNOGRID_ABI = [
    {
        "name": "recordAttack",
        "type": "function",
        "inputs": [
            {"name": "attackType", "type": "string"},
            {"name": "deviceId",   "type": "string"},
            {"name": "sector",     "type": "string"},
            {"name": "severity",   "type": "uint8"},
            {"name": "detectedBy", "type": "string"},
            {"name": "rawData",    "type": "string"},
        ],
        "outputs": [{"name": "recordId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "isPatternKnown",
        "type": "function",
        "inputs": [
            {"name": "attackType", "type": "string"},
            {"name": "sector",     "type": "string"},
        ],
        "outputs": [{"name": "count", "type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "name": "getStats",
        "type": "function",
        "inputs": [],
        "outputs": [
            {"name": "_totalAttacks",      "type": "uint256"},
            {"name": "_totalMorphogenesis","type": "uint256"},
            {"name": "_honeypotCount",     "type": "uint256"},
            {"name": "_fpSensitivityBps",  "type": "uint256"},
            {"name": "_chainVersion",      "type": "uint256"},
        ],
        "stateMutability": "view",
    },
    {
        "name": "isSectorIsolated",
        "type": "function",
        "inputs": [{"name": "sector", "type": "string"}],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
    },
    {
        "name": "isDeviceQuarantined",
        "type": "function",
        "inputs": [{"name": "deviceId", "type": "string"}],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
    },
]

KEY_REGISTRY_ABI = [
    {
        "name": "registerDevice",
        "type": "function",
        "inputs": [
            {"name": "deviceId",  "type": "string"},
            {"name": "kemKeyHash","type": "bytes32"},
            {"name": "sigKeyHash","type": "bytes32"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "name": "verifyKey",
        "type": "function",
        "inputs": [
            {"name": "deviceId",  "type": "string"},
            {"name": "kemKeyHash","type": "bytes32"},
            {"name": "sigKeyHash","type": "bytes32"},
        ],
        "outputs": [
            {"name": "valid",  "type": "bool"},
            {"name": "reason", "type": "string"},
        ],
        "stateMutability": "view",
    },
]

FL_REGISTRY_ABI = [
    {
        "name": "commitModelVersion",
        "type": "function",
        "inputs": [
            {"name": "modelHash",         "type": "bytes32"},
            {"name": "gradientsHash",     "type": "bytes32"},
            {"name": "accuracyBps",       "type": "uint256"},
            {"name": "lossBps",           "type": "uint256"},
            {"name": "participants",      "type": "uint256"},
            {"name": "imaginationsCount", "type": "uint256"},
        ],
        "outputs": [{"name": "roundNumber", "type": "uint256"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "verifyModel",
        "type": "function",
        "inputs": [{"name": "modelHash", "type": "bytes32"}],
        "outputs": [{"name": "valid", "type": "bool"}],
        "stateMutability": "view",
    },
    {
        "name": "getStats",
        "type": "function",
        "inputs": [],
        "outputs": [
            {"name": "_currentRound",           "type": "uint256"},
            {"name": "_totalImaginations",      "type": "uint256"},
            {"name": "_latestAccuracyBps",      "type": "uint256"},
            {"name": "_latestPoisoningDetected","type": "bool"},
        ],
        "stateMutability": "view",
    },
]

HONEYPOT_ABI = [
    {
        "name": "fileReport",
        "type": "function",
        "inputs": [
            {"name": "attackerHash",       "type": "bytes32"},
            {"name": "attackType",         "type": "string"},
            {"name": "sector",             "type": "string"},
            {"name": "interactionCount",   "type": "uint256"},
            {"name": "behaviorHash",       "type": "bytes32"},
            {"name": "aiSamplesGenerated", "type": "uint256"},
        ],
        "outputs": [{"name": "reportId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "isKnownAttacker",
        "type": "function",
        "inputs": [{"name": "attackerHash", "type": "bytes32"}],
        "outputs": [
            {"name": "known",    "type": "bool"},
            {"name": "attempts", "type": "uint256"},
        ],
        "stateMutability": "view",
    },
    {
        "name": "getStats",
        "type": "function",
        "inputs": [],
        "outputs": [
            {"name": "_totalReports",  "type": "uint256"},
            {"name": "_totalAiSamples","type": "uint256"},
            {"name": "_totalAttackers","type": "uint256"},
            {"name": "_activeThreats", "type": "uint256"},
        ],
        "stateMutability": "view",
    },
]


# ── In-Memory Simulation ──────────────────────────────────────────────────────

class SimulationLedger:
    """
    In-memory simulation of the Solidity contracts.
    Used when Web3 is not available or contracts not deployed.
    """
    def __init__(self):
        self.attacks:         dict = {}
        self.keys:            dict = {}
        self.fl_rounds:       dict = {}
        self.honeypot_reports:dict = {}
        self.pattern_counts:  dict = {}
        self.attack_count     = 0
        self.fl_round         = 0
        self.honeypot_count   = 5
        self.fp_sensitivity   = 9200
        self.morphogenesis    = 0


# ── Web3 Bridge ───────────────────────────────────────────────────────────────

class ImmunoGridWeb3Bridge:
    """
    Bridge between Python backend and Solidity smart contracts.
    Automatically falls back to simulation if blockchain unavailable.
    """

    SEVERITY_MAP = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        contracts: Optional[Dict[str, str]] = None,
        private_key: Optional[str] = None,
    ):
        self.rpc_url     = rpc_url or os.getenv("BLOCKCHAIN_RPC_URL", "http://localhost:8545")
        self.private_key = private_key or os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")
        self.contracts   = contracts or self._load_deployment()
        self.sim         = SimulationLedger()
        self.mode        = "simulation"

        if WEB3_AVAILABLE and self.private_key and self.contracts:
            self._init_web3()
        else:
            logger.info("web3_bridge_simulation_mode",
                        reason="no_web3" if not WEB3_AVAILABLE else "no_private_key")

    def _load_deployment(self) -> Dict[str, str]:
        """Load deployed contract addresses from JSON file."""
        path = Path(__file__).parent / "solidity" / "deployments" / "hardhat.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                return data.get("contracts", {})
        return {}

    def _init_web3(self):
        """Initialize Web3 connection and contract instances."""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Cannot connect to {self.rpc_url}")

            # POA middleware for Besu/Ganache
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            self.account = self.w3.eth.account.from_key(self.private_key)

            # Instantiate contracts
            self.immunogrid_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contracts.get("ImmunoGrid", "")),
                abi=IMMUNOGRID_ABI,
            )
            self.key_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contracts.get("ImmunoGridKeyRegistry", "")),
                abi=KEY_REGISTRY_ABI,
            )
            self.fl_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contracts.get("ImmunoGridFL", "")),
                abi=FL_REGISTRY_ABI,
            )
            self.honeypot_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contracts.get("ImmunoGridHoneypot", "")),
                abi=HONEYPOT_ABI,
            )

            self.mode = "web3"
            logger.info("web3_bridge_connected", rpc=self.rpc_url, mode="web3")

        except Exception as e:
            logger.warning("web3_bridge_fallback", error=str(e), mode="simulation")
            self.mode = "simulation"

    def _send_tx(self, fn) -> Optional[str]:
        """Build, sign, and send a transaction. Returns tx hash."""
        try:
            nonce  = self.w3.eth.get_transaction_count(self.account.address)
            gas    = fn.estimate_gas({"from": self.account.address})
            tx     = fn.build_transaction({
                "from":     self.account.address,
                "nonce":    nonce,
                "gas":      int(gas * 1.2),
                "gasPrice": self.w3.eth.gas_price,
            })
            signed = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt.transactionHash.hex()
        except Exception as e:
            logger.error("tx_failed", error=str(e))
            return None

    # ── Public API ────────────────────────────────────────────────────────────

    def record_attack(
        self,
        attack_type: str,
        device_id:   str,
        sector:      str,
        severity:    str,
        detected_by: str,
    ) -> Dict[str, Any]:
        """Record an attack — on-chain or simulation."""
        sev_int  = self.SEVERITY_MAP.get(severity.lower(), 1)
        raw_data = f"{attack_type}:{device_id}:{sector}:{datetime.utcnow().isoformat()}"

        if self.mode == "web3":
            fn = self.immunogrid_contract.functions.recordAttack(
                attack_type, device_id, sector, sev_int, detected_by, raw_data
            )
            tx_hash = self._send_tx(fn)
            return {
                "mode": "web3",
                "tx_hash": tx_hash,
                "attack_type": attack_type,
                "sector": sector,
            }

        # Simulation
        self.sim.attack_count += 1
        record_id = hashlib.sha256(raw_data.encode()).hexdigest()
        self.sim.attacks[record_id] = {
            "record_id": record_id, "attack_type": attack_type,
            "device_id": device_id, "sector": sector, "severity": severity,
            "detected_by": detected_by, "timestamp": datetime.utcnow().isoformat(),
        }
        key = f"{attack_type}:{sector}"
        self.sim.pattern_counts[key] = self.sim.pattern_counts.get(key, 0) + 1
        self.sim.morphogenesis += 1
        return {"mode": "simulation", "record_id": record_id, "attack_type": attack_type}

    def register_device_key(
        self,
        device_id:   str,
        kem_pubkey:  bytes,
        sig_pubkey:  bytes,
    ) -> Dict[str, Any]:
        """Register device PQC keys on-chain."""
        kem_hash = bytes.fromhex(hashlib.sha256(kem_pubkey).hexdigest())
        sig_hash = bytes.fromhex(hashlib.sha256(sig_pubkey).hexdigest())

        if self.mode == "web3":
            fn = self.key_contract.functions.registerDevice(
                device_id, kem_hash, sig_hash
            )
            tx_hash = self._send_tx(fn)
            return {"mode": "web3", "tx_hash": tx_hash, "device_id": device_id}

        self.sim.keys[device_id] = {"kem_hash": kem_hash.hex(), "sig_hash": sig_hash.hex()}
        return {"mode": "simulation", "device_id": device_id, "registered": True}

    def verify_device_key(
        self,
        device_id:   str,
        kem_pubkey:  bytes,
        sig_pubkey:  bytes,
    ) -> Tuple[bool, str]:
        """Verify device keys against on-chain registry."""
        kem_hash = bytes.fromhex(hashlib.sha256(kem_pubkey).hexdigest())
        sig_hash = bytes.fromhex(hashlib.sha256(sig_pubkey).hexdigest())

        if self.mode == "web3":
            try:
                return self.key_contract.functions.verifyKey(
                    device_id, kem_hash, sig_hash
                ).call()
            except Exception as e:
                return (False, str(e))

        stored = self.sim.keys.get(device_id)
        if not stored:
            return (False, "Device not registered")
        if stored["kem_hash"] == kem_hash.hex() and stored["sig_hash"] == sig_hash.hex():
            return (True, "Valid")
        return (False, "Key mismatch")

    def commit_fl_model(
        self,
        model_hash:          str,
        gradients_hash:      str,
        accuracy_pct:        float,
        loss:                float,
        participants:        int,
        imaginations_count:  int,
    ) -> Dict[str, Any]:
        """Commit FL model version to blockchain."""
        model_bh = bytes.fromhex(hashlib.sha256(model_hash.encode()).hexdigest())
        grad_bh  = bytes.fromhex(hashlib.sha256(gradients_hash.encode()).hexdigest())
        acc_bps  = int(accuracy_pct * 100)
        loss_bps = int(loss * 10000)

        if self.mode == "web3":
            fn = self.fl_contract.functions.commitModelVersion(
                model_bh, grad_bh, acc_bps, loss_bps, participants, imaginations_count
            )
            tx_hash = self._send_tx(fn)
            return {"mode": "web3", "tx_hash": tx_hash, "accuracy_bps": acc_bps}

        self.sim.fl_round += 1
        self.sim.fl_rounds[self.sim.fl_round] = {
            "model_hash": model_hash, "accuracy": accuracy_pct,
            "participants": participants, "imaginations": imaginations_count,
        }
        return {
            "mode": "simulation",
            "round": self.sim.fl_round,
            "accuracy": accuracy_pct,
        }

    def file_honeypot_report(
        self,
        attacker_id:          str,
        attack_type:          str,
        sector:               str,
        interaction_count:    int,
        behavior_signature:   dict,
        ai_samples_generated: int,
    ) -> Dict[str, Any]:
        """File honeypot intelligence report on-chain."""
        attacker_hash = bytes.fromhex(hashlib.sha256(attacker_id.encode()).hexdigest())
        behavior_hash = bytes.fromhex(
            hashlib.sha256(json.dumps(behavior_signature, sort_keys=True).encode()).hexdigest()
        )

        if self.mode == "web3":
            fn = self.honeypot_contract.functions.fileReport(
                attacker_hash, attack_type, sector,
                interaction_count, behavior_hash, ai_samples_generated,
            )
            tx_hash = self._send_tx(fn)
            return {"mode": "web3", "tx_hash": tx_hash}

        report_id = hashlib.sha256(f"{attacker_id}{datetime.utcnow()}".encode()).hexdigest()
        self.sim.honeypot_reports[report_id] = {
            "attacker": attacker_id, "attack_type": attack_type, "sector": sector,
            "interactions": interaction_count, "ai_samples": ai_samples_generated,
        }
        return {"mode": "simulation", "report_id": report_id}

    def is_pattern_known(self, attack_type: str, sector: str) -> Tuple[bool, int]:
        """Check if attack pattern is known."""
        if self.mode == "web3":
            try:
                count = self.immunogrid_contract.functions.isPatternKnown(
                    attack_type, sector
                ).call()
                return count > 0, count
            except Exception:
                pass

        key   = f"{attack_type}:{sector}"
        count = self.sim.pattern_counts.get(key, 0)
        return count > 0, count

    def get_contract_stats(self) -> Dict[str, Any]:
        """Get statistics from all contracts."""
        if self.mode == "web3":
            try:
                ig   = self.immunogrid_contract.functions.getStats().call()
                fl   = self.fl_contract.functions.getStats().call()
                hp   = self.honeypot_contract.functions.getStats().call()
                return {
                    "mode": "web3",
                    "immunogrid":  {"total_attacks": ig[0], "morphogenesis": ig[1],
                                    "honeypots": ig[2], "fp_sensitivity_bps": ig[3]},
                    "fl_registry": {"current_round": fl[0], "total_imaginations": fl[1],
                                    "latest_accuracy_bps": fl[2], "poisoning_detected": fl[3]},
                    "honeypot":    {"total_reports": hp[0], "ai_samples": hp[1],
                                    "total_attackers": hp[2], "active_threats": hp[3]},
                }
            except Exception as e:
                logger.error("contract_stats_failed", error=str(e))

        return {
            "mode":        "simulation",
            "immunogrid":  {"total_attacks": self.sim.attack_count,
                            "morphogenesis": self.sim.morphogenesis,
                            "honeypots":     self.sim.honeypot_count,
                            "fp_sensitivity_bps": self.sim.fp_sensitivity},
            "fl_registry": {"current_round": self.sim.fl_round},
            "honeypot":    {"total_reports": len(self.sim.honeypot_reports)},
        }
