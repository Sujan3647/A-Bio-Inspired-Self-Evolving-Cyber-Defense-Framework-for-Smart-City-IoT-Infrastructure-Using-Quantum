/*
ImmunoGrid — Hyperledger Fabric Chaincode Unit Tests
Tests helper functions, structs, and morphogenesis logic.

Run:
    go test ./... -v
*/

package main

import (
	"crypto/sha256"
	"fmt"
	"testing"
)

// ── Struct Tests ───────────────────────────────────────────────────────────────

func TestAttackRecordStruct(t *testing.T) {
	r := AttackRecord{
		RecordID:   "ATK-000001",
		AttackType: "spoofing",
		DeviceID:   "traffic-sensor-001",
		Sector:     "traffic",
		Severity:   "high",
		DetectedBy: "quantum_fingerprint",
		Timestamp:  "2026-07-23T00:00:00Z",
		DataHash:   "abc123",
	}
	if r.AttackType != "spoofing"           { t.Errorf("AttackType mismatch") }
	if r.DeviceID  != "traffic-sensor-001"  { t.Errorf("DeviceID mismatch") }
	if r.Sector    != "traffic"             { t.Errorf("Sector mismatch") }
	if r.Severity  != "high"               { t.Errorf("Severity mismatch") }
	t.Logf("PASS: AttackRecord struct")
}

func TestNetworkTopologyStruct(t *testing.T) {
	topo := NetworkTopology{
		ActiveSectors:      []string{"traffic", "hospital", "water", "power"},
		IsolatedSectors:    []string{},
		QuarantinedDevices: []string{},
		HoneypotCount:      5,
		FPSensitivity:      0.92,
		FirewallRules:      map[string]string{},
		MorphogenesisCount: 0,
	}
	if len(topo.ActiveSectors) != 4 { t.Errorf("expected 4 sectors") }
	if topo.HoneypotCount != 5     { t.Errorf("expected 5 honeypots") }
	if topo.FPSensitivity != 0.92  { t.Errorf("expected 0.92 fp sensitivity") }
	t.Logf("PASS: NetworkTopology struct")
}

// ── Helper Function Tests ──────────────────────────────────────────────────────

func TestContains(t *testing.T) {
	slice := []string{"traffic", "hospital", "water"}
	if !contains(slice, "traffic") { t.Error("should contain traffic") }
	if !contains(slice, "hospital"){ t.Error("should contain hospital") }
	if  contains(slice, "power")   { t.Error("should not contain power") }
	if  contains(slice, "")        { t.Error("should not contain empty") }
	t.Logf("PASS: contains()")
}

func TestRemove(t *testing.T) {
	slice := []string{"traffic", "hospital", "water"}

	result := remove(slice, "hospital")
	if len(result) != 2         { t.Errorf("expected 2 elements, got %d", len(result)) }
	if contains(result,"hospital"){ t.Error("hospital should be removed") }
	if !contains(result,"traffic"){ t.Error("traffic should remain") }
	if !contains(result,"water")  { t.Error("water should remain") }

	// Remove nonexistent
	result2 := remove(slice, "nonexistent")
	if len(result2) != 3 { t.Errorf("removing nonexistent should not change length") }
	t.Logf("PASS: remove()")
}

func TestUnique(t *testing.T) {
	slice  := []string{"a","b","a","c","b","a","d"}
	result := unique(slice)
	if len(result) != 4 { t.Errorf("expected 4 unique, got %d: %v", len(result), result) }
	t.Logf("PASS: unique()")
}

func TestUniquePreservesOrder(t *testing.T) {
	slice  := []string{"broadcast_alert","spawn_honeypots","broadcast_alert"}
	result := unique(slice)
	if len(result) != 2 { t.Errorf("expected 2, got %d", len(result)) }
	if result[0] != "broadcast_alert"  { t.Error("first should be broadcast_alert") }
	if result[1] != "spawn_honeypots"  { t.Error("second should be spawn_honeypots") }
	t.Logf("PASS: unique() preserves order")
}

// ── Morphogenesis Tests ────────────────────────────────────────────────────────

func TestAllAttacksHaveBroadcastAlert(t *testing.T) {
	attacks    := []string{"spoofing","ddos","data_poisoning","replay_attack","ransomware","man_in_the_middle"}
	severities := []string{"low","medium","high","critical"}
	for _, atk := range attacks {
		for _, sev := range severities {
			actions := determineMorphogenesisActions(atk, sev)
			found := false
			for _, a := range actions { if a=="broadcast_alert" { found=true; break } }
			if !found { t.Errorf("attack=%s sev=%s missing broadcast_alert", atk, sev) }
		}
	}
	t.Logf("PASS: all attacks include broadcast_alert")
}

func TestSpoofingHighHasHoneypots(t *testing.T) {
	actions := determineMorphogenesisActions("spoofing","high")
	honeypots := false; fp := false
	for _, a := range actions {
		if a=="spawn_honeypots"         { honeypots=true }
		if a=="increase_fp_sensitivity" { fp=true }
	}
	if !honeypots { t.Error("spoofing high should spawn honeypots") }
	if !fp        { t.Error("spoofing high should increase fp sensitivity") }
	t.Logf("PASS: spoofing high → honeypots + fp sensitivity")
}

func TestSpoofingHighQuarantinesDevice(t *testing.T) {
	actions := determineMorphogenesisActions("spoofing","high")
	found := false
	for _, a := range actions { if a=="quarantine_device" { found=true; break } }
	if !found { t.Error("spoofing high should quarantine device") }
	t.Logf("PASS: spoofing high → quarantine_device")
}

func TestSpoofingLowNoQuarantine(t *testing.T) {
	actions := determineMorphogenesisActions("spoofing","low")
	for _, a := range actions {
		if a=="quarantine_device" { t.Error("spoofing low should NOT quarantine") }
	}
	t.Logf("PASS: spoofing low → no quarantine")
}

func TestDDoSCriticalIsolatesSector(t *testing.T) {
	actions := determineMorphogenesisActions("ddos","critical")
	found := false
	for _, a := range actions { if a=="isolate_sector" { found=true; break } }
	if !found { t.Errorf("ddos critical should isolate sector, got: %v", actions) }
	t.Logf("PASS: ddos critical → isolate_sector")
}

func TestDDoSMediumNoIsolation(t *testing.T) {
	actions := determineMorphogenesisActions("ddos","medium")
	for _, a := range actions {
		if a=="isolate_sector" { t.Error("ddos medium should NOT isolate sector") }
	}
	t.Logf("PASS: ddos medium → no isolate_sector")
}

func TestDDoSAlwaysUpdatesFirewall(t *testing.T) {
	for _, sev := range []string{"low","medium","high","critical"} {
		actions := determineMorphogenesisActions("ddos", sev)
		found := false
		for _, a := range actions { if a=="update_firewall" { found=true; break } }
		if !found { t.Errorf("ddos %s should update_firewall", sev) }
	}
	t.Logf("PASS: ddos always → update_firewall")
}

func TestDataPoisoningQuarantinesDevice(t *testing.T) {
	actions := determineMorphogenesisActions("data_poisoning","high")
	found := false
	for _, a := range actions { if a=="quarantine_device" { found=true; break } }
	if !found { t.Error("data_poisoning high should quarantine device") }
	t.Logf("PASS: data_poisoning → quarantine_device")
}

func TestRansomwareQuarantinesDevice(t *testing.T) {
	actions := determineMorphogenesisActions("ransomware","critical")
	found := false
	for _, a := range actions { if a=="quarantine_device" { found=true; break } }
	if !found { t.Error("ransomware critical should quarantine device") }
	t.Logf("PASS: ransomware → quarantine_device")
}

func TestNoDuplicateActions(t *testing.T) {
	attacks    := []string{"spoofing","ddos","data_poisoning","replay_attack","ransomware"}
	severities := []string{"low","medium","high","critical"}
	for _, atk := range attacks {
		for _, sev := range severities {
			actions := determineMorphogenesisActions(atk, sev)
			seen := map[string]bool{}
			for _, a := range actions {
				if seen[a] { t.Errorf("duplicate action '%s' for %s/%s", a, atk, sev) }
				seen[a] = true
			}
		}
	}
	t.Logf("PASS: no duplicate morphogenesis actions")
}

// ── Pattern Key Tests ──────────────────────────────────────────────────────────

func TestPatternKeyFormat(t *testing.T) {
	key := fmt.Sprintf("%s:%s", "spoofing", "traffic")
	if key != "spoofing:traffic" { t.Errorf("expected 'spoofing:traffic', got '%s'", key) }
	t.Logf("PASS: pattern key format")
}

// ── Hash Tests ────────────────────────────────────────────────────────────────

func TestSHA256Consistency(t *testing.T) {
	data  := []byte("spoofing:dev-001:traffic:2026-07-23")
	hash1 := fmt.Sprintf("%x", sha256.Sum256(data))
	hash2 := fmt.Sprintf("%x", sha256.Sum256(data))
	if hash1 != hash2    { t.Error("SHA-256 should be deterministic") }
	if len(hash1) != 64  { t.Errorf("SHA-256 hex should be 64 chars, got %d", len(hash1)) }
	t.Logf("PASS: SHA-256 consistency, len=%d", len(hash1))
}

func TestDifferentDataDifferentHash(t *testing.T) {
	h1 := fmt.Sprintf("%x", sha256.Sum256([]byte("data1")))
	h2 := fmt.Sprintf("%x", sha256.Sum256([]byte("data2")))
	if h1 == h2 { t.Error("different data should produce different hashes") }
	t.Logf("PASS: different data → different hashes")
}

// ── Attack Severity Coverage ───────────────────────────────────────────────────

func TestAllSeveritiesHandled(t *testing.T) {
	// Every attack type must return at least 1 action for every severity
	attacks    := []string{"spoofing","ddos","data_poisoning","replay_attack","ransomware","man_in_the_middle","unknown_attack"}
	severities := []string{"low","medium","high","critical"}
	for _, atk := range attacks {
		for _, sev := range severities {
			actions := determineMorphogenesisActions(atk, sev)
			if len(actions) == 0 {
				t.Errorf("attack=%s sev=%s returned no actions", atk, sev)
			}
		}
	}
	t.Logf("PASS: all attack/severity combinations return actions")
}

// ── LedgerStats Tests ─────────────────────────────────────────────────────────

func TestLedgerStatsStruct(t *testing.T) {
	stats := LedgerStats{
		TotalAttacks:       42,
		TotalMorphogenesis: 38,
		LastRecordID:       "ATK-000042",
		Timestamp:          "2026-07-23T12:00:00Z",
	}
	if stats.TotalAttacks != 42       { t.Error("TotalAttacks mismatch") }
	if stats.TotalMorphogenesis != 38 { t.Error("TotalMorphogenesis mismatch") }
	if stats.LastRecordID != "ATK-000042" { t.Error("LastRecordID mismatch") }
	t.Logf("PASS: LedgerStats struct")
}
