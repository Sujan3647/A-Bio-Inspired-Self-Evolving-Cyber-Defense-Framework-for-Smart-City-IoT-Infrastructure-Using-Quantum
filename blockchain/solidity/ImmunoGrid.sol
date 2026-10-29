// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImmunoGrid — Morphogenetic Blockchain Smart Contract
 * @notice Bio-Inspired Smart City Cyber Defense — Immune Memory
 * @dev Records attack events immutably and triggers network morphogenesis
 *
 * Deployed on: Ethereum (testnet) / Hyperledger Besu / Polygon
 *
 * Features:
 * - Immutable attack record storage
 * - Automatic morphogenesis (network topology restructuring)
 * - Role-based access (only authorized nodes can write)
 * - Attack pattern recognition (same attack = instant alert)
 * - Government-grade audit trail
 * - Event emission for real-time dashboard updates
 */

contract ImmunoGrid {

    // ── Enums ─────────────────────────────────────────────────────────────────

    enum Severity { LOW, MEDIUM, HIGH, CRITICAL }

    enum MorphogenesisAction {
        BROADCAST_ALERT,
        SPAWN_HONEYPOTS,
        ISOLATE_SECTOR,
        QUARANTINE_DEVICE,
        UPDATE_FIREWALL,
        INCREASE_FP_SENSITIVITY,
        REROUTE_TRAFFIC
    }

    // ── Structs ───────────────────────────────────────────────────────────────

    struct AttackRecord {
        bytes32 recordId;
        string  attackType;
        string  deviceId;
        string  sector;
        Severity severity;
        string  detectedBy;
        uint256 timestamp;
        bytes32 dataHash;
        bool    morphogenesisTriggered;
        string[] responseActions;
    }

    struct NetworkTopology {
        string[] activeSectors;
        string[] isolatedSectors;
        string[] quarantinedDevices;
        uint256  honeypotCount;
        uint256  fpSensitivityBps;   // basis points: 9200 = 92.00%
        uint256  morphogenesisCount;
        uint256  lastModified;
    }

    struct NodeInfo {
        address nodeAddress;
        string  orgName;
        bool    isAuthorized;
        bool    isActive;
        uint256 recordsSubmitted;
    }

    // ── State Variables ───────────────────────────────────────────────────────

    address public owner;
    uint256 public totalAttacks;
    uint256 public chainVersion;

    mapping(bytes32 => AttackRecord) public attackRecords;
    mapping(string  => uint256)      public attackPatternCount;   // "spoofing:hospital" => count
    mapping(address => NodeInfo)     public authorizedNodes;
    mapping(string  => bool)         public isolatedSectors;
    mapping(string  => bool)         public quarantinedDevices;

    bytes32[] public recordIndex;   // All record IDs in order
    NetworkTopology public topology;

    // ── Events ────────────────────────────────────────────────────────────────

    /// @notice Emitted when a new attack is recorded
    event AttackRecorded(
        bytes32 indexed recordId,
        string  attackType,
        string  sector,
        Severity severity,
        uint256 timestamp,
        bool    morphogenesisTriggered
    );

    /// @notice Emitted when network morphogenesis is executed
    event MorphogenesisExecuted(
        string  action,
        string  sector,
        string  deviceId,
        uint256 timestamp
    );

    /// @notice Emitted when a sector is isolated
    event SectorIsolated(string sector, uint256 timestamp);

    /// @notice Emitted when a device is quarantined
    event DeviceQuarantined(string deviceId, uint256 timestamp);

    /// @notice Emitted when honeypots are spawned
    event HonepotsSpawned(uint256 count, string sector, uint256 timestamp);

    /// @notice Emitted when quantum FP sensitivity increases
    event FPSensitivityIncreased(uint256 newSensitivityBps, uint256 timestamp);

    /// @notice Emitted when a node is authorized
    event NodeAuthorized(address indexed nodeAddress, string orgName);

    // ── Modifiers ─────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "ImmunoGrid: Not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(
            authorizedNodes[msg.sender].isAuthorized &&
            authorizedNodes[msg.sender].isActive,
            "ImmunoGrid: Not an authorized node"
        );
        _;
    }

    modifier validSeverity(uint8 sev) {
        require(sev <= 3, "ImmunoGrid: Invalid severity level");
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        chainVersion = 1;

        // Initialize network topology
        topology.honeypotCount      = 5;
        topology.fpSensitivityBps   = 9200;  // 92.00%
        topology.morphogenesisCount = 0;
        topology.lastModified       = block.timestamp;

        // Owner is first authorized node
        authorizedNodes[msg.sender] = NodeInfo({
            nodeAddress:      msg.sender,
            orgName:          "ImmunoGridOrg1",
            isAuthorized:     true,
            isActive:         true,
            recordsSubmitted: 0
        });

        emit NodeAuthorized(msg.sender, "ImmunoGridOrg1");
    }

    // ── Core Functions ────────────────────────────────────────────────────────

    /**
     * @notice Record an attack event on the immutable ledger
     * @param attackType  Type of attack (spoofing, ddos, etc.)
     * @param deviceId    Target device ID
     * @param sector      City sector (traffic, hospital, etc.)
     * @param severity    0=LOW, 1=MEDIUM, 2=HIGH, 3=CRITICAL
     * @param detectedBy  Detection mechanism (quantum_fingerprint, ai_brain, honeypot)
     * @param rawData     Raw attack data for hash generation
     * @return recordId   The unique immutable record ID
     */
    function recordAttack(
        string calldata attackType,
        string calldata deviceId,
        string calldata sector,
        uint8           severity,
        string calldata detectedBy,
        string calldata rawData
    )
        external
        onlyAuthorized
        validSeverity(severity)
        returns (bytes32 recordId)
    {
        totalAttacks++;

        // Generate unique record ID
        recordId = keccak256(abi.encodePacked(
            attackType, deviceId, sector, block.timestamp, totalAttacks
        ));

        // Compute data hash for integrity
        bytes32 dataHash = keccak256(abi.encodePacked(rawData));

        // Determine morphogenesis actions
        string[] memory actions = _getMorphogenesisActions(attackType, severity);
        bool morphNeeded = actions.length > 0;

        // Store record
        attackRecords[recordId] = AttackRecord({
            recordId:               recordId,
            attackType:             attackType,
            deviceId:               deviceId,
            sector:                 sector,
            severity:               Severity(severity),
            detectedBy:             detectedBy,
            timestamp:              block.timestamp,
            dataHash:               dataHash,
            morphogenesisTriggered: morphNeeded,
            responseActions:        actions
        });

        recordIndex.push(recordId);

        // Track attack patterns
        string memory patternKey = string(abi.encodePacked(attackType, ":", sector));
        attackPatternCount[patternKey]++;

        // Execute morphogenesis
        if (morphNeeded) {
            _executeMorphogenesis(actions, sector, deviceId);
        }

        // Update node stats
        authorizedNodes[msg.sender].recordsSubmitted++;

        emit AttackRecorded(
            recordId, attackType, sector, Severity(severity),
            block.timestamp, morphNeeded
        );

        return recordId;
    }

    /**
     * @notice Check if an attack pattern has been seen before
     * @param attackType  Attack type string
     * @param sector      City sector
     * @return count  Number of times this pattern was seen (0 = never)
     */
    function isPatternKnown(
        string calldata attackType,
        string calldata sector
    ) external view returns (uint256 count) {
        string memory key = string(abi.encodePacked(attackType, ":", sector));
        return attackPatternCount[key];
    }

    /**
     * @notice Get a specific attack record
     */
    function getAttackRecord(bytes32 recordId)
        external
        view
        returns (AttackRecord memory)
    {
        require(attackRecords[recordId].timestamp > 0, "ImmunoGrid: Record not found");
        return attackRecords[recordId];
    }

    /**
     * @notice Get total number of records
     */
    function getTotalRecords() external view returns (uint256) {
        return recordIndex.length;
    }

    /**
     * @notice Get network topology state
     */
    function getTopology() external view returns (NetworkTopology memory) {
        return topology;
    }

    /**
     * @notice Get all record IDs (paginated)
     */
    function getRecordIds(uint256 start, uint256 limit)
        external
        view
        returns (bytes32[] memory)
    {
        uint256 end = start + limit;
        if (end > recordIndex.length) end = recordIndex.length;
        bytes32[] memory ids = new bytes32[](end - start);
        for (uint256 i = start; i < end; i++) {
            ids[i - start] = recordIndex[i];
        }
        return ids;
    }

    // ── Morphogenesis Engine ──────────────────────────────────────────────────

    /**
     * @dev Determine morphogenesis response actions for an attack
     */
    function _getMorphogenesisActions(
        string memory attackType,
        uint8 severity
    ) internal pure returns (string[] memory actions) {
        // All attacks get a broadcast alert
        uint256 count = 1;
        if (_streq(attackType, "spoofing")) {
            count = severity >= 2 ? 4 : 3;  // HIGH+ adds quarantine
        } else if (_streq(attackType, "ddos")) {
            count = severity == 3 ? 4 : 3;  // CRITICAL adds isolation
        } else if (_streq(attackType, "data_poisoning") || _streq(attackType, "mitm")) {
            count = 3;
        } else if (_streq(attackType, "replay_attack") || _streq(attackType, "ransomware")) {
            count = 3;
        }

        actions = new string[](count);
        actions[0] = "broadcast_alert";

        if (_streq(attackType, "spoofing")) {
            actions[1] = "increase_fp_sensitivity";
            actions[2] = "spawn_honeypots";
            if (count == 4) actions[3] = "quarantine_device";
        } else if (_streq(attackType, "ddos")) {
            actions[1] = "update_firewall";
            actions[2] = "reroute_traffic";
            if (count == 4) actions[3] = "isolate_sector";
        } else if (_streq(attackType, "data_poisoning") || _streq(attackType, "mitm")) {
            actions[1] = "quarantine_device";
            actions[2] = "update_firewall";
        } else {
            actions[1] = "quarantine_device";
            actions[2] = "spawn_honeypots";
        }

        return actions;
    }

    /**
     * @dev Execute morphogenesis actions and update topology
     */
    function _executeMorphogenesis(
        string[] memory actions,
        string memory sector,
        string memory deviceId
    ) internal {
        topology.morphogenesisCount++;
        topology.lastModified = block.timestamp;

        for (uint256 i = 0; i < actions.length; i++) {
            string memory action = actions[i];

            if (_streq(action, "isolate_sector")) {
                isolatedSectors[sector] = true;
                emit SectorIsolated(sector, block.timestamp);
                emit MorphogenesisExecuted("isolate_sector", sector, deviceId, block.timestamp);

            } else if (_streq(action, "quarantine_device")) {
                quarantinedDevices[deviceId] = true;
                emit DeviceQuarantined(deviceId, block.timestamp);
                emit MorphogenesisExecuted("quarantine_device", sector, deviceId, block.timestamp);

            } else if (_streq(action, "spawn_honeypots")) {
                topology.honeypotCount += 2;
                emit HonepotsSpawned(2, sector, block.timestamp);
                emit MorphogenesisExecuted("spawn_honeypots", sector, deviceId, block.timestamp);

            } else if (_streq(action, "increase_fp_sensitivity")) {
                // Decrease threshold by 2% (more sensitive)
                if (topology.fpSensitivityBps > 7500) {
                    topology.fpSensitivityBps -= 200;
                }
                emit FPSensitivityIncreased(topology.fpSensitivityBps, block.timestamp);
                emit MorphogenesisExecuted("increase_fp_sensitivity", sector, deviceId, block.timestamp);

            } else if (_streq(action, "update_firewall")) {
                emit MorphogenesisExecuted("update_firewall", sector, deviceId, block.timestamp);

            } else if (_streq(action, "reroute_traffic")) {
                emit MorphogenesisExecuted("reroute_traffic", sector, deviceId, block.timestamp);

            } else if (_streq(action, "broadcast_alert")) {
                emit MorphogenesisExecuted("broadcast_alert", sector, deviceId, block.timestamp);
            }
        }
    }

    // ── Admin Functions ───────────────────────────────────────────────────────

    /**
     * @notice Authorize a new node to write attack records
     */
    function authorizeNode(address nodeAddr, string calldata orgName)
        external onlyOwner
    {
        authorizedNodes[nodeAddr] = NodeInfo({
            nodeAddress:      nodeAddr,
            orgName:          orgName,
            isAuthorized:     true,
            isActive:         true,
            recordsSubmitted: 0
        });
        emit NodeAuthorized(nodeAddr, orgName);
    }

    /**
     * @notice Revoke a node's authorization
     */
    function revokeNode(address nodeAddr) external onlyOwner {
        authorizedNodes[nodeAddr].isAuthorized = false;
    }

    /**
     * @notice Restore a quarantined device
     */
    function restoreDevice(string calldata deviceId)
        external onlyAuthorized
    {
        quarantinedDevices[deviceId] = false;
    }

    /**
     * @notice Restore an isolated sector
     */
    function restoreSector(string calldata sector)
        external onlyAuthorized
    {
        isolatedSectors[sector] = false;
    }

    /**
     * @notice Check if a device is quarantined
     */
    function isDeviceQuarantined(string calldata deviceId)
        external view returns (bool)
    {
        return quarantinedDevices[deviceId];
    }

    /**
     * @notice Check if a sector is isolated
     */
    function isSectorIsolated(string calldata sector)
        external view returns (bool)
    {
        return isolatedSectors[sector];
    }

    // ── Helper ────────────────────────────────────────────────────────────────

    /**
     * @dev String equality comparison
     */
    function _streq(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    /**
     * @notice Get contract stats
     */
    function getStats() external view returns (
        uint256 _totalAttacks,
        uint256 _totalMorphogenesis,
        uint256 _honeypotCount,
        uint256 _fpSensitivityBps,
        uint256 _chainVersion
    ) {
        return (
            totalAttacks,
            topology.morphogenesisCount,
            topology.honeypotCount,
            topology.fpSensitivityBps,
            chainVersion
        );
    }
}
