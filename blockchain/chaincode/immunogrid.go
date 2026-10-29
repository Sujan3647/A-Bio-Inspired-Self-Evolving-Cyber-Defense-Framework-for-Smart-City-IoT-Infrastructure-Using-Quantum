/*
ImmunoGrid — Hyperledger Fabric Chaincode (Go)
Morphogenetic Blockchain for Smart City IoT Cyber Defense.

Deploy on Hyperledger Fabric:
    peer chaincode install -n immunogrid -v 1.0 -l golang -p immunogrid/chaincode
    peer chaincode instantiate -n immunogrid -v 1.0 -C immunogrid-channel -c '{"Args":["InitLedger"]}'

Functions:
    InitLedger           — initialize with default network topology
    RecordAttack         — write attack to immutable ledger + trigger morphogenesis
    GetAttackRecord      — retrieve single attack record by ID
    GetNetworkTopology   — current defense topology state
    GetStats             — ledger statistics
*/

package main

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// ── Data Structures ───────────────────────────────────────────────────────────

// AttackRecord is an immutable ledger entry for a detected attack.
type AttackRecord struct {
	RecordID             string            `json:"record_id"`
	AttackType           string            `json:"attack_type"`
	DeviceID             string            `json:"device_id"`
	Sector               string            `json:"sector"`
	Severity             string            `json:"severity"`  // "low"|"medium"|"high"|"critical"
	AttackerSignature    map[string]string `json:"attacker_signature"`
	DetectedBy           string            `json:"detected_by"`
	MorphogenesisActions []string          `json:"morphogenesis_actions"`
	Timestamp            string            `json:"timestamp"`
	DataHash             string            `json:"data_hash"`
}

// NetworkTopology represents the current defense configuration.
type NetworkTopology struct {
	ActiveSectors       []string          `json:"active_sectors"`
	IsolatedSectors     []string          `json:"isolated_sectors"`
	QuarantinedDevices  []string          `json:"quarantined_devices"`
	HoneypotCount       int               `json:"honeypot_count"`
	FPSensitivity       float64           `json:"fp_sensitivity"`   // 0.75 – 0.99
	FirewallRules       map[string]string `json:"firewall_rules"`
	MorphogenesisCount  int               `json:"morphogenesis_count"`
	LastModified        string            `json:"last_modified"`
}

// LedgerStats aggregates overall ledger statistics.
type LedgerStats struct {
	TotalAttacks       int    `json:"total_attacks"`
	TotalMorphogenesis int    `json:"total_morphogenesis"`
	LastRecordID       string `json:"last_record_id"`
	Timestamp          string `json:"timestamp"`
}

// ImmunoGridContract is the main chaincode struct.
type ImmunoGridContract struct {
	contractapi.Contract
}

// ── Chaincode Init ────────────────────────────────────────────────────────────

// InitLedger initialises the blockchain with a default network topology.
func (c *ImmunoGridContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	topology := NetworkTopology{
		ActiveSectors: []string{
			"traffic", "hospital", "water", "power",
			"surveillance", "metro", "airport", "government",
		},
		IsolatedSectors:    []string{},
		QuarantinedDevices: []string{},
		HoneypotCount:      5,
		FPSensitivity:      0.92,
		FirewallRules:      map[string]string{},
		MorphogenesisCount: 0,
		LastModified:       time.Now().UTC().Format(time.RFC3339),
	}

	topologyBytes, err := json.Marshal(topology)
	if err != nil {
		return fmt.Errorf("failed to marshal topology: %v", err)
	}
	if err = ctx.GetStub().PutState("NETWORK_TOPOLOGY", topologyBytes); err != nil {
		return fmt.Errorf("failed to store topology: %v", err)
	}

	stats := LedgerStats{
		TotalAttacks:       0,
		TotalMorphogenesis: 0,
		LastRecordID:       "GENESIS",
		Timestamp:          time.Now().UTC().Format(time.RFC3339),
	}
	statsBytes, _ := json.Marshal(stats)
	return ctx.GetStub().PutState("LEDGER_STATS", statsBytes)
}

// ── Core Functions ────────────────────────────────────────────────────────────

// RecordAttack writes an immutable attack record and triggers morphogenesis.
func (c *ImmunoGridContract) RecordAttack(
	ctx         contractapi.TransactionContextInterface,
	attackType  string,
	deviceID    string,
	sector      string,
	severity    string,
	detectedBy  string,
	attackerSig string,
) (*AttackRecord, error) {

	// Load and update stats
	statsBytes, _ := ctx.GetStub().GetState("LEDGER_STATS")
	var stats LedgerStats
	json.Unmarshal(statsBytes, &stats)
	stats.TotalAttacks++

	recordID := fmt.Sprintf("ATK-%012d", stats.TotalAttacks)

	// Determine morphogenesis actions
	actions := determineMorphogenesisActions(attackType, severity)

	// Build data hash
	rawData := fmt.Sprintf("%s%s%s%s%s", attackType, deviceID, sector, severity, detectedBy)
	dataHash := fmt.Sprintf("%x", sha256.Sum256([]byte(rawData)))

	// Deserialise attacker signature (optional JSON object)
	var sig map[string]string
	if attackerSig != "" {
		json.Unmarshal([]byte(attackerSig), &sig)
	}

	record := AttackRecord{
		RecordID:             recordID,
		AttackType:           attackType,
		DeviceID:             deviceID,
		Sector:               sector,
		Severity:             severity,
		DetectedBy:           detectedBy,
		AttackerSignature:    sig,
		MorphogenesisActions: actions,
		Timestamp:            time.Now().UTC().Format(time.RFC3339),
		DataHash:             dataHash,
	}

	recordBytes, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal record: %v", err)
	}
	if err = ctx.GetStub().PutState(recordID, recordBytes); err != nil {
		return nil, fmt.Errorf("failed to store record: %v", err)
	}

	// Execute morphogenesis
	if len(actions) > 0 {
		if err = c.executeMorphogenesis(ctx, actions, sector, deviceID); err != nil {
			return nil, fmt.Errorf("morphogenesis failed: %v", err)
		}
	}

	// Persist updated stats
	stats.LastRecordID = recordID
	stats.Timestamp    = record.Timestamp
	statsBytes, _       = json.Marshal(stats)
	ctx.GetStub().PutState("LEDGER_STATS", statsBytes)

	// Emit event for subscribers
	ctx.GetStub().SetEvent("AttackRecorded", recordBytes)

	return &record, nil
}

// GetAttackRecord retrieves a single attack record by ID.
func (c *ImmunoGridContract) GetAttackRecord(
	ctx      contractapi.TransactionContextInterface,
	recordID string,
) (*AttackRecord, error) {
	recordBytes, err := ctx.GetStub().GetState(recordID)
	if err != nil {
		return nil, fmt.Errorf("failed to read record: %v", err)
	}
	if recordBytes == nil {
		return nil, fmt.Errorf("record %s does not exist", recordID)
	}
	var record AttackRecord
	if err = json.Unmarshal(recordBytes, &record); err != nil {
		return nil, fmt.Errorf("failed to unmarshal record: %v", err)
	}
	return &record, nil
}

// GetNetworkTopology returns the current defence topology.
func (c *ImmunoGridContract) GetNetworkTopology(
	ctx contractapi.TransactionContextInterface,
) (*NetworkTopology, error) {
	topologyBytes, err := ctx.GetStub().GetState("NETWORK_TOPOLOGY")
	if err != nil {
		return nil, fmt.Errorf("failed to read topology: %v", err)
	}
	var topology NetworkTopology
	json.Unmarshal(topologyBytes, &topology)
	return &topology, nil
}

// GetStats returns overall ledger statistics.
func (c *ImmunoGridContract) GetStats(
	ctx contractapi.TransactionContextInterface,
) (*LedgerStats, error) {
	statsBytes, err := ctx.GetStub().GetState("LEDGER_STATS")
	if err != nil {
		return nil, err
	}
	var stats LedgerStats
	json.Unmarshal(statsBytes, &stats)
	return &stats, nil
}

// ── Morphogenesis Engine ──────────────────────────────────────────────────────

// determineMorphogenesisActions maps (attackType, severity) → list of actions.
// Also exported via test_go_helpers for unit testing.
func determineMorphogenesisActions(attackType, severity string) []string {
	actions := []string{"broadcast_alert"}

	switch attackType {
	case "spoofing":
		actions = append(actions, "increase_fp_sensitivity", "spawn_honeypots")
		if severity == "high" || severity == "critical" {
			actions = append(actions, "quarantine_device")
		}
	case "ddos":
		actions = append(actions, "update_firewall", "reroute_traffic")
		if severity == "critical" {
			actions = append(actions, "isolate_sector")
		}
	case "data_poisoning", "man_in_the_middle":
		actions = append(actions, "quarantine_device", "update_firewall")
	case "replay_attack", "ransomware":
		actions = append(actions, "quarantine_device", "spawn_honeypots")
	default:
		actions = append(actions, "quarantine_device", "spawn_honeypots")
	}

	return unique(actions)
}

// executeMorphogenesis applies the actions to the stored NetworkTopology.
func (c *ImmunoGridContract) executeMorphogenesis(
	ctx      contractapi.TransactionContextInterface,
	actions  []string,
	sector   string,
	deviceID string,
) error {
	topologyBytes, _ := ctx.GetStub().GetState("NETWORK_TOPOLOGY")
	var topology NetworkTopology
	json.Unmarshal(topologyBytes, &topology)

	for _, action := range actions {
		switch action {
		case "isolate_sector":
			if !contains(topology.IsolatedSectors, sector) {
				topology.IsolatedSectors = append(topology.IsolatedSectors, sector)
				topology.ActiveSectors   = remove(topology.ActiveSectors, sector)
			}
		case "quarantine_device":
			if !contains(topology.QuarantinedDevices, deviceID) {
				topology.QuarantinedDevices = append(topology.QuarantinedDevices, deviceID)
			}
		case "spawn_honeypots":
			topology.HoneypotCount += 2
		case "increase_fp_sensitivity":
			if topology.FPSensitivity > 0.75 {
				topology.FPSensitivity -= 0.02
			}
		case "update_firewall":
			if topology.FirewallRules == nil {
				topology.FirewallRules = make(map[string]string)
			}
			topology.FirewallRules[sector] = "rate_limit:100/min,block_unknown:true"
		}
	}

	topology.MorphogenesisCount++
	topology.LastModified = time.Now().UTC().Format(time.RFC3339)

	topologyBytes, err := json.Marshal(topology)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState("NETWORK_TOPOLOGY", topologyBytes)
}

// ── Slice Helpers ─────────────────────────────────────────────────────────────

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func remove(slice []string, item string) []string {
	result := []string{}
	for _, s := range slice {
		if s != item {
			result = append(result, s)
		}
	}
	return result
}

func unique(slice []string) []string {
	seen   := map[string]bool{}
	result := []string{}
	for _, s := range slice {
		if !seen[s] {
			seen[s] = true
			result  = append(result, s)
		}
	}
	return result
}

// ── Main ──────────────────────────────────────────────────────────────────────

func main() {
	chaincode, err := contractapi.NewChaincode(&ImmunoGridContract{})
	if err != nil {
		fmt.Printf("Error creating ImmunoGrid chaincode: %v\n", err)
		return
	}
	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting ImmunoGrid chaincode: %v\n", err)
	}
}
