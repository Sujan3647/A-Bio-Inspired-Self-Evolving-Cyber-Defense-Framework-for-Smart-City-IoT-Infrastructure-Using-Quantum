"""
ImmunoGrid — Complete Blockchain Test Suite
Tests all blockchain components: Python, Solidity (sim), PBFT, Web3 Bridge

Run:
    python test_blockchain_complete.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'iot_simulator'))

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
results = []


def check(name: str, fn):
    try:
        fn()
        results.append((name, True, ""))
        console.print(f"  [green]✅ {name}[/green]")
    except Exception as e:
        results.append((name, False, str(e)[:80]))
        console.print(f"  [red]❌ {name}: {str(e)[:70]}[/red]")


console.print("\n[bold cyan]╔═════════════════════════════════════════════════╗[/bold cyan]")
console.print("[bold cyan]║  ImmunoGrid Blockchain — Complete Test Suite   ║[/bold cyan]")
console.print("[bold cyan]╚═════════════════════════════════════════════════╝[/bold cyan]\n")

# ── 1. Immune Ledger ──────────────────────────────────────────────────────────
console.print("[cyan]1. Morphogenetic Blockchain (Immune Ledger)[/cyan]")

from blockchain.immune_ledger import MorphogeneticBlockchain

def t_genesis():
    bc = MorphogeneticBlockchain(difficulty=1)
    assert len(bc.chain) == 1
    assert bc.chain[0].index == 0
    assert bc.is_chain_valid()
check("Genesis block creation + validity", t_genesis)

def t_record_all_attacks():
    bc = MorphogeneticBlockchain(difficulty=1)
    attack_types = ['spoofing','ddos','data_poisoning','replay_attack','ransomware','man_in_the_middle']
    for atk in attack_types:
        r = bc.record_attack(atk, 'dev-001', 'hospital', {}, 'quantum', 'high')
        assert r.record_id.startswith('ATK-')
        assert r.morphogenesis_triggered
    stats = bc.get_stats()
    assert stats['total_attacks_recorded'] == 6
    assert stats['morphogenesis_events'] >= 6
    assert bc.is_chain_valid()
check("Record 6 attack types + all morphogenesis", t_record_all_attacks)

def t_immune_memory():
    bc = MorphogeneticBlockchain(difficulty=1)
    bc.record_attack('spoofing','d1','traffic',{},'q','high')
    bc.record_attack('spoofing','d2','traffic',{},'q','high')
    bc.record_attack('ddos','d3','hospital',{},'ai','critical')
    known_s, count_s = bc.is_attack_pattern_known('spoofing', 'traffic')
    known_d, count_d = bc.is_attack_pattern_known('ddos', 'hospital')
    unknown, count_u  = bc.is_attack_pattern_known('ransomware', 'water')
    assert known_s and count_s == 2
    assert known_d and count_d == 1
    assert not unknown and count_u == 0
check("Immune memory pattern recognition", t_immune_memory)

def t_attack_history():
    bc = MorphogeneticBlockchain(difficulty=1)
    bc.record_attack('ddos','d1','hospital',{},'ai','critical')
    bc.record_attack('spoofing','d2','traffic',{},'q','high')
    history = bc.get_attack_history()
    assert len(history) == 2
    hospital_only = bc.get_attack_history(sector='hospital')
    assert len(hospital_only) == 1
    # Accept either key
    record = hospital_only[0]
    sec = record.get('sector') or record.get('target_sector')
    assert sec == 'hospital'
    assert record['attack_type'] == 'ddos'
check("Attack history query (all + filtered)", t_attack_history)

def t_tampering_detection():
    bc = MorphogeneticBlockchain(difficulty=1)
    bc.record_attack('spoofing','d1','traffic',{},'q','high')
    assert bc.is_chain_valid()
    # Tamper
    bc.chain[1].block_hash = 'deadbeef' * 8
    assert not bc.is_chain_valid()
check("Chain integrity — tampering detection", t_tampering_detection)

def t_topology_spoofing():
    bc = MorphogeneticBlockchain(difficulty=1)
    bc.record_attack('spoofing','dev-007','water',{},'quantum','high')
    topo = bc.topology
    assert 'dev-007' in topo.quarantined_devices
    assert topo.honeypot_count > 5
    assert topo.fingerprint_sensitivity < 0.92
check("Morphogenesis: quarantine + honeypots on spoofing", t_topology_spoofing)

def t_topology_ddos_critical():
    bc = MorphogeneticBlockchain(difficulty=1)
    bc.record_attack('ddos','dev-008','power',{},'ai','critical')
    topo = bc.topology
    assert 'power' in topo.isolated_sectors
check("Morphogenesis: sector isolation on critical DDoS", t_topology_ddos_critical)

def t_sector_restore():
    bc = MorphogeneticBlockchain(difficulty=1)
    bc.record_attack('ddos','dev-009','metro',{},'ai','critical')
    assert 'metro' in bc.topology.isolated_sectors
    bc.topology.isolated_sectors.remove('metro')
    assert 'metro' not in bc.topology.isolated_sectors
check("Sector restore after isolation", t_sector_restore)

def t_multiple_rounds():
    bc = MorphogeneticBlockchain(difficulty=1)
    for i in range(20):
        bc.record_attack('spoofing', f'dev-{i:03d}', 'traffic', {}, 'quantum', 'medium')
    stats = bc.get_stats()
    assert stats['total_attacks_recorded'] == 20
    assert bc.is_chain_valid()
check("20 attack records — chain remains valid", t_multiple_rounds)

# ── 2. Smart Contract (Python Simulation) ────────────────────────────────────
console.print("\n[cyan]2. ImmunoGrid Smart Contract (Python simulation of Solidity)[/cyan]")

from blockchain.smart_contract import ImmunoGridChaincode, MorphogenesisType

def t_sc_basic():
    cc = ImmunoGridChaincode()
    r = cc.record_attack('spoofing','dev-001','traffic','high',{},'quantum')
    assert r['attack_id'].startswith('ATK-')
    assert 'broadcast_alert' in r['morphogenesis_actions']
    assert cc.verify_chain_integrity()['is_valid']
check("SC: record attack + actions + chain valid", t_sc_basic)

def t_sc_all_types():
    cc = ImmunoGridChaincode()
    for atk in ['spoofing','ddos','data_poisoning','replay_attack','ransomware','man_in_the_middle']:
        r = cc.record_attack(atk, 'dev-x', 'hospital', 'critical', {}, 'quantum')
        assert r['attack_id'].startswith('ATK-')
    assert cc.world_state['attack_count'] == 6
    assert cc.verify_chain_integrity()['is_valid']
check("SC: 6 attack types all recorded", t_sc_all_types)

def t_sc_ddos_isolation():
    cc = ImmunoGridChaincode()
    cc.record_attack('ddos','dev-002','hospital','critical',{},'ai')
    topo = cc.get_network_topology()
    assert 'hospital' in topo['isolated_sectors']
check("SC: DDoS critical → sector isolated", t_sc_ddos_isolation)

def t_sc_spoofing_quarantine():
    cc = ImmunoGridChaincode()
    cc.record_attack('spoofing','dev-003','water','high',{},'quantum')
    topo = cc.get_network_topology()
    assert 'dev-003' in topo['quarantined_devices']
check("SC: Spoofing high → device quarantined", t_sc_spoofing_quarantine)

def t_sc_fp_sensitivity():
    cc = ImmunoGridChaincode()
    initial = cc.world_state['network_topology']['fp_sensitivity']
    cc.record_attack('spoofing','dev-004','traffic','medium',{},'quantum')
    after = cc.get_network_topology()['fp_sensitivity']
    assert after < initial
check("SC: Spoofing → FP sensitivity increases", t_sc_fp_sensitivity)

def t_sc_honeypots():
    cc = ImmunoGridChaincode()
    initial_hp = cc.get_network_topology()['honeypot_count']
    cc.record_attack('spoofing','dev-005','metro','high',{},'quantum')
    after_hp = cc.get_network_topology()['honeypot_count']
    assert after_hp > initial_hp
check("SC: Spoofing → honeypots spawned", t_sc_honeypots)

def t_sc_pattern():
    cc = ImmunoGridChaincode()
    cc.record_attack('ddos','d1','power','high',{},'ai')
    cc.record_attack('ddos','d2','power','medium',{},'ai')
    known, count = cc.is_attack_pattern_known('ddos','power')
    assert known and count == 2
check("SC: Pattern recognition across 2 attacks", t_sc_pattern)

def t_sc_stats():
    cc = ImmunoGridChaincode()
    for i in range(10):
        cc.record_attack('ransomware',f'd{i}','airport','critical',{},'ai')
    s = cc.get_stats()
    assert s['attack_records'] == 10
    assert s['chain_valid']
    assert s['morphogenesis_events'] == 10
check("SC: 10 attacks + stats correct", t_sc_stats)

# ── 3. PBFT Consensus ─────────────────────────────────────────────────────────
console.print("\n[cyan]3. PBFT Byzantine Fault-Tolerant Consensus[/cyan]")

from blockchain.consensus import PBFTConsensus, NodeStatus

def t_pbft_init():
    pbft = PBFTConsensus(num_nodes=4)
    assert pbft.f == 1
    assert pbft.quorum == 3
    health = pbft.get_network_health()
    assert health['healthy'] == 4
    assert health['quorum_possible']
check("PBFT: 4-node init (f=1, quorum=3)", t_pbft_init)

def t_pbft_7_nodes():
    pbft = PBFTConsensus(num_nodes=7)
    assert pbft.f == 2
    assert pbft.quorum == 5
check("PBFT: 7-node network (f=2, quorum=5)", t_pbft_7_nodes)

def t_pbft_all_healthy():
    pbft = PBFTConsensus(num_nodes=4)
    for i in range(5):
        result = pbft.propose_transaction({'round': i, 'attack': 'spoofing'})
        assert result.reached
    s = pbft.get_stats()
    assert s['total_rounds'] == 5
    assert s['successful'] == 5
    assert s['success_rate'] == 100.0
check("PBFT: 5 rounds, all 4 nodes healthy → 100%", t_pbft_all_healthy)

def t_pbft_one_byzantine():
    pbft = PBFTConsensus(num_nodes=4)
    pbft.simulate_byzantine_attack(0)
    result = pbft.propose_transaction({'attack': 'ddos', 'device': 'dev-001'})
    assert result.reached          # 1 byzantine, 3 honest → still reaches quorum=3
    assert result.faulty_nodes >= 1
    assert pbft.byzantine_detected >= 1
check("PBFT: 1 Byzantine node → consensus still reached", t_pbft_one_byzantine)

def t_pbft_heal_node():
    pbft = PBFTConsensus(num_nodes=4)
    pbft.simulate_byzantine_attack(1)
    pbft.heal_node(1)
    result = pbft.propose_transaction({'attack': 'test'})
    assert result.reached
check("PBFT: heal node after Byzantine attack", t_pbft_heal_node)

def t_pbft_network_health():
    pbft = PBFTConsensus(num_nodes=4)
    pbft.simulate_byzantine_attack(0)
    health = pbft.get_network_health()
    assert health['byzantine'] == 1
    assert health['healthy'] == 3
check("PBFT: network health report accurate", t_pbft_network_health)

# ── 4. Web3 Bridge ────────────────────────────────────────────────────────────
console.print("\n[cyan]4. Web3 Bridge (Simulation Mode)[/cyan]")

from blockchain.web3_bridge import ImmunoGridWeb3Bridge

def t_bridge_mode():
    bridge = ImmunoGridWeb3Bridge()
    assert bridge.mode == 'simulation'
check("Web3 Bridge: initializes in simulation mode", t_bridge_mode)

def t_bridge_record():
    bridge = ImmunoGridWeb3Bridge()
    r = bridge.record_attack('spoofing','dev-001','traffic','high','quantum')
    assert r['mode'] == 'simulation'
    assert 'record_id' in r
    assert len(r['record_id']) == 64  # SHA-256 hex
check("Web3 Bridge: record_attack returns record_id", t_bridge_record)

def t_bridge_pattern():
    bridge = ImmunoGridWeb3Bridge()
    bridge.record_attack('ddos','d1','hospital','critical','ai')
    bridge.record_attack('ddos','d2','hospital','critical','ai')
    known, count = bridge.is_pattern_known('ddos','hospital')
    assert known and count == 2
check("Web3 Bridge: pattern recognition", t_bridge_pattern)

def t_bridge_fl():
    bridge = ImmunoGridWeb3Bridge()
    r = bridge.commit_fl_model('model-v1','grads-v1',97.2,0.11,492,1204)
    assert r['round'] == 1
    assert r['accuracy'] == 97.2
    r2 = bridge.commit_fl_model('model-v2','grads-v2',97.8,0.09,495,1350)
    assert r2['round'] == 2
check("Web3 Bridge: FL model commit (2 rounds)", t_bridge_fl)

def t_bridge_honeypot():
    bridge = ImmunoGridWeb3Bridge()
    r = bridge.file_honeypot_report('atk-001','spoofing','traffic',5,{'sig':0.9},12)
    assert 'report_id' in r
    assert len(r['report_id']) == 64
check("Web3 Bridge: honeypot intelligence report", t_bridge_honeypot)

def t_bridge_keys():
    import os as _os
    bridge = ImmunoGridWeb3Bridge()
    kem_key = _os.urandom(64)
    sig_key = _os.urandom(96)
    bridge.register_device_key('dev-key-test', kem_key, sig_key)
    valid, reason = bridge.verify_device_key('dev-key-test', kem_key, sig_key)
    assert valid and reason == 'Valid'
    bad_valid, _ = bridge.verify_device_key('dev-key-test', _os.urandom(64), sig_key)
    assert not bad_valid
    unknown, _ = bridge.verify_device_key('not-registered', kem_key, sig_key)
    assert not unknown
check("Web3 Bridge: PQC key register + verify + reject impostor", t_bridge_keys)

def t_bridge_stats():
    bridge = ImmunoGridWeb3Bridge()
    for atk in ['spoofing','ddos','data_poisoning']:
        bridge.record_attack(atk,'d1','traffic','high','quantum')
    bridge.commit_fl_model('model','grads',97.0,0.12,490,1100)
    bridge.file_honeypot_report('a1','spoofing','traffic',3,{},6)
    stats = bridge.get_contract_stats()
    assert stats['immunogrid']['total_attacks'] == 3
    assert stats['fl_registry']['current_round'] == 1
    assert stats['honeypot']['total_reports'] == 1
check("Web3 Bridge: get_contract_stats aggregation", t_bridge_stats)

# ── 5. Blockchain + IoT Integration ──────────────────────────────────────────
console.print("\n[cyan]5. Blockchain + IoT + Quantum Integration[/cyan]")

def t_full_pipeline():
    from iot_simulator.devices import TrafficSensor, HospitalDevice, PowerSensor
    from quantum_engine.fingerprint_gen import QuantumFingerprintEngine
    from blockchain.immune_ledger import MorphogeneticBlockchain
    from honeypot.decoy_spawner import HoneypotNetwork

    bc = MorphogeneticBlockchain(difficulty=1)
    qe = QuantumFingerprintEngine(num_qubits=4)
    hp = HoneypotNetwork()

    devices = [
        TrafficSensor(location='z1', sector='traffic'),
        HospitalDevice(location='z2', sector='hospital'),
        PowerSensor(location='z3', sector='power'),
    ]
    for d in devices:
        qe.register_device(d.device_id, d.get_fingerprint_vector())

    # Simulate 3 attacks through full pipeline
    for device in devices:
        # QF check
        result = qe.verify_device(device.device_id, device.get_fingerprint_vector())
        assert result.is_authentic

        # Record on blockchain
        rec = bc.record_attack('spoofing', device.device_id, device.sector, {}, 'quantum', 'high')
        assert rec.record_id.startswith('ATK-')

        # Spawn honeypots
        decoys = hp.spawn_honeypots(device.device_id, device.sector, count=2)
        assert len(decoys) == 2

    assert bc.get_stats()['total_attacks_recorded'] == 3
    assert bc.is_chain_valid()
    assert hp.get_stats()['active_honeypots'] == 6
check("Full pipeline: IoT→QF→Blockchain→Honeypot (3 devices)", t_full_pipeline)

def t_consensus_blockchain():
    bc = MorphogeneticBlockchain(difficulty=1)
    pbft = PBFTConsensus(num_nodes=4)

    attacks = [
        ('spoofing',   'dev-a', 'traffic',  'high',     {}, 'quantum'),
        ('ddos',       'dev-b', 'hospital', 'critical', {}, 'ai'),
        ('ransomware', 'dev-c', 'power',    'critical', {}, 'honeypot'),
    ]

    for atk_type, device, sector, severity, sig, detected_by in attacks:
        # PBFT consensus before writing to blockchain
        tx = {'attack_type': atk_type, 'device': device, 'sector': sector}
        consensus = pbft.propose_transaction(tx)
        assert consensus.reached, f"Consensus failed for {atk_type}"
        # Write to chain only after consensus
        bc.record_attack(atk_type, device, sector, sig, detected_by, severity)

    assert bc.get_stats()['total_attacks_recorded'] == 3
    assert bc.is_chain_valid()
    assert pbft.get_stats()['successful'] == 3
check("PBFT consensus → blockchain write (3 rounds)", t_consensus_blockchain)

def t_web3_bridge_full():
    bridge = ImmunoGridWeb3Bridge()
    from blockchain.immune_ledger import MorphogeneticBlockchain
    bc = MorphogeneticBlockchain(difficulty=1)

    # Record through both bridge (Solidity sim) and immune ledger (Python)
    attacks = [('spoofing','traffic','high'), ('ddos','hospital','critical'), ('ransomware','power','critical')]
    for atk, sec, sev in attacks:
        bridge.record_attack(atk, f'{sec}-dev-001', sec, sev, 'quantum')
        bc.record_attack(atk, f'{sec}-dev-001', sec, {}, 'quantum', sev)

    b_stats = bridge.get_contract_stats()
    bc_stats = bc.get_stats()

    assert b_stats['immunogrid']['total_attacks'] == 3
    assert bc_stats['total_attacks_recorded'] == 3
    assert bc.is_chain_valid()
check("Web3 Bridge + Immune Ledger synchronized", t_web3_bridge_full)

# ── Summary ───────────────────────────────────────────────────────────────────

passed  = sum(1 for _, ok, _ in results if ok)
failed  = sum(1 for _, ok, _ in results if not ok)

table = Table(
    title=f"\nBlockchain Test Results — {passed}/{len(results)} passed",
    box=box.ROUNDED,
    border_style="cyan",
)
table.add_column("Test",   style="white")
table.add_column("Status", style="bold")
table.add_column("Notes",  style="dim")

for name, ok, err in results:
    table.add_row(
        name,
        "[green]PASS ✅[/green]" if ok else "[red]FAIL ❌[/red]",
        err or ""
    )

console.print(table)

if failed == 0:
    console.print(f"\n[bold green]🎉 ALL {passed} BLOCKCHAIN TESTS PASSED[/bold green]\n")
    console.print("[dim]Solidity contracts ready:[/dim]")
    console.print("[cyan]  blockchain/solidity/ImmunoGrid.sol[/cyan]")
    console.print("[cyan]  blockchain/solidity/ImmunoGridKey.sol[/cyan]")
    console.print("[cyan]  blockchain/solidity/ImmunoGridFL.sol[/cyan]")
    console.print("[cyan]  blockchain/solidity/ImmunoGridHoneypot.sol[/cyan]")
    console.print("[cyan]  blockchain/solidity/ImmunoGridAccess.sol[/cyan]")
    console.print("[cyan]  blockchain/solidity/ImmunoGridOracle.sol[/cyan]")
    console.print("\n[dim]Deploy: cd blockchain/solidity && npm install && npx hardhat test[/dim]\n")
else:
    console.print(f"\n[bold red]{failed} test(s) failed.[/bold red]\n")
    import sys; sys.exit(1)
