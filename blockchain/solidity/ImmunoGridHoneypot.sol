// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImmunoGrid Honeypot Intelligence Registry
 * @notice On-chain storage for honeypot-captured attacker profiles
 * @dev When a honeypot traps an attacker, the intelligence report
 *      is committed on-chain permanently. This creates an immutable
 *      global threat intelligence database that all smart cities can use.
 */

contract ImmunoGridHoneypot {

    // ── Structs ───────────────────────────────────────────────────────────────

    struct AttackerProfile {
        bytes32  profileHash;       // Hash of full behavioral profile
        string   primaryAttack;     // Most common attack type
        string   targetSector;      // Most targeted sector
        uint256  totalAttempts;     // Total attack attempts captured
        uint256  firstSeen;         // First interaction timestamp
        uint256  lastSeen;          // Last interaction timestamp
        bool     isActive;          // Still considered an active threat
        address  reportedBy;        // Node that reported this
    }

    struct HoneypotReport {
        bytes32  reportId;
        bytes32  attackerHash;      // Attacker identifier (anonymized)
        string   attackType;
        string   sector;
        uint256  interactionCount;
        bytes32  behaviorHash;      // Hash of behavioral signature
        uint256  aiSamplesGenerated;
        uint256  timestamp;
    }

    // ── State ─────────────────────────────────────────────────────────────────

    address public owner;

    mapping(bytes32 => AttackerProfile) public attackerProfiles;
    mapping(bytes32 => HoneypotReport)  public honeypotReports;

    bytes32[] public reportIndex;
    bytes32[] public attackerIndex;

    uint256 public totalReports;
    uint256 public totalAiSamples;
    uint256 public totalAttackersProfiled;

    // ── Events ────────────────────────────────────────────────────────────────

    event HoneypotReportFiled(
        bytes32 indexed reportId,
        string  attackType,
        string  sector,
        uint256 interactions,
        uint256 aiSamples
    );

    event NewAttackerProfiled(
        bytes32 indexed attackerHash,
        string  primaryAttack,
        uint256 timestamp
    );

    event ThreatIntelUpdated(
        bytes32 indexed attackerHash,
        uint256 totalAttempts,
        uint256 timestamp
    );

    // ── Modifier ─────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Honeypot: Not owner");
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
    }

    // ── Core Functions ────────────────────────────────────────────────────────

    /**
     * @notice File a honeypot intelligence report
     * @param attackerHash       Anonymized attacker identifier hash
     * @param attackType         Type of attack attempted
     * @param sector             Target sector
     * @param interactionCount   Number of captured interactions
     * @param behaviorHash       Hash of captured behavioral signature
     * @param aiSamplesGenerated Number of AI training samples generated
     */
    function fileReport(
        bytes32 attackerHash,
        string  calldata attackType,
        string  calldata sector,
        uint256 interactionCount,
        bytes32 behaviorHash,
        uint256 aiSamplesGenerated
    ) external onlyOwner returns (bytes32 reportId) {
        reportId = keccak256(abi.encodePacked(
            attackerHash, attackType, sector, block.timestamp, totalReports
        ));

        honeypotReports[reportId] = HoneypotReport({
            reportId:           reportId,
            attackerHash:       attackerHash,
            attackType:         attackType,
            sector:             sector,
            interactionCount:   interactionCount,
            behaviorHash:       behaviorHash,
            aiSamplesGenerated: aiSamplesGenerated,
            timestamp:          block.timestamp
        });

        reportIndex.push(reportId);
        totalReports++;
        totalAiSamples += aiSamplesGenerated;

        // Update or create attacker profile
        if (attackerProfiles[attackerHash].firstSeen == 0) {
            // New attacker
            attackerProfiles[attackerHash] = AttackerProfile({
                profileHash:    behaviorHash,
                primaryAttack:  attackType,
                targetSector:   sector,
                totalAttempts:  interactionCount,
                firstSeen:      block.timestamp,
                lastSeen:       block.timestamp,
                isActive:       true,
                reportedBy:     msg.sender
            });
            attackerIndex.push(attackerHash);
            totalAttackersProfiled++;
            emit NewAttackerProfiled(attackerHash, attackType, block.timestamp);
        } else {
            // Known attacker — update profile
            AttackerProfile storage ap = attackerProfiles[attackerHash];
            ap.totalAttempts += interactionCount;
            ap.lastSeen       = block.timestamp;
            emit ThreatIntelUpdated(attackerHash, ap.totalAttempts, block.timestamp);
        }

        emit HoneypotReportFiled(reportId, attackType, sector, interactionCount, aiSamplesGenerated);
        return reportId;
    }

    /**
     * @notice Check if an attacker hash is known
     */
    function isKnownAttacker(bytes32 attackerHash)
        external view returns (bool known, uint256 attempts)
    {
        AttackerProfile memory ap = attackerProfiles[attackerHash];
        return (ap.firstSeen > 0, ap.totalAttempts);
    }

    /**
     * @notice Get a honeypot report
     */
    function getReport(bytes32 reportId)
        external view returns (HoneypotReport memory)
    {
        require(honeypotReports[reportId].timestamp > 0, "Report not found");
        return honeypotReports[reportId];
    }

    /**
     * @notice Get platform statistics
     */
    function getStats() external view returns (
        uint256 _totalReports,
        uint256 _totalAiSamples,
        uint256 _totalAttackers,
        uint256 _activeThreats
    ) {
        uint256 active = 0;
        for (uint256 i = 0; i < attackerIndex.length; i++) {
            if (attackerProfiles[attackerIndex[i]].isActive) active++;
        }
        return (totalReports, totalAiSamples, totalAttackersProfiled, active);
    }
}
