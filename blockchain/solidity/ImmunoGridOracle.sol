// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImmunoGrid Threat Oracle
 * @notice On-chain threat intelligence oracle for smart contracts.
 *         Exposes real-time threat scores and device trust levels
 *         so other contracts can query ImmunoGrid security data.
 *
 * Use cases:
 * - A smart meter contract checks if its sector is under attack
 * - A hospital contract verifies device trust before accepting data
 * - Insurance contracts adjust premiums based on threat level
 * - Government contracts trigger emergency protocols automatically
 *
 * Data updated by: Authorized ImmunoGrid nodes after each detection event
 */

interface IImmunoGrid {
    function isPatternKnown(string calldata, string calldata) external view returns (uint256);
    function isSectorIsolated(string calldata) external view returns (bool);
    function isDeviceQuarantined(string calldata) external view returns (bool);
    function totalAttacks() external view returns (uint256);
}

contract ImmunoGridOracle {

    // ── Structs ───────────────────────────────────────────────────────────────

    struct ThreatLevel {
        uint8   level;          // 0=NONE 1=LOW 2=MEDIUM 3=HIGH 4=CRITICAL
        uint256 score;          // 0-10000 (higher = more dangerous)
        uint256 lastUpdated;
        uint256 attackCount24h;
        bool    underActiveAttack;
    }

    struct DeviceTrust {
        string  deviceId;
        uint256 trustScore;     // 0-10000 (10000 = fully trusted)
        bool    isTrusted;
        uint256 lastVerified;
        uint256 fpFidelity;     // Quantum fingerprint fidelity × 10000
    }

    // ── State ─────────────────────────────────────────────────────────────────

    address public owner;
    IImmunoGrid public immunoGridContract;

    // Sector threat levels
    mapping(string => ThreatLevel) public sectorThreat;

    // Device trust scores
    mapping(string => DeviceTrust) public deviceTrust;

    // Global threat score (0-10000)
    uint256 public globalThreatScore;
    uint256 public lastGlobalUpdate;

    // Subscribers who get notified on threat changes
    mapping(address => bool) public subscribers;
    address[] public subscriberList;

    // ── Events ────────────────────────────────────────────────────────────────

    event ThreatLevelUpdated(
        string  indexed sector,
        uint8   oldLevel,
        uint8   newLevel,
        uint256 score,
        uint256 timestamp
    );

    event DeviceTrustUpdated(
        string  indexed deviceId,
        uint256 trustScore,
        bool    isTrusted,
        uint256 fpFidelity,
        uint256 timestamp
    );

    event GlobalThreatUpdated(
        uint256 oldScore,
        uint256 newScore,
        uint256 timestamp
    );

    event CriticalAlert(
        string  sector,
        string  attackType,
        uint256 timestamp
    );

    event NewSubscriber(address indexed subscriber, uint256 timestamp);

    // ── Modifier ─────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Oracle: Not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == owner ||
            subscribers[msg.sender],
            "Oracle: Not authorized"
        );
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor(address _immunoGridAddr) {
        owner = msg.sender;
        if (_immunoGridAddr != address(0)) {
            immunoGridContract = IImmunoGrid(_immunoGridAddr);
        }

        // Initialize all sectors as safe
        string[8] memory sectors = [
            "traffic","hospital","water","power",
            "surveillance","metro","airport","government"
        ];
        for (uint256 i = 0; i < sectors.length; i++) {
            sectorThreat[sectors[i]] = ThreatLevel({
                level: 0,
                score: 0,
                lastUpdated: block.timestamp,
                attackCount24h: 0,
                underActiveAttack: false
            });
        }

        globalThreatScore = 0;
        lastGlobalUpdate  = block.timestamp;
    }

    // ── Oracle Update Functions ───────────────────────────────────────────────

    /**
     * @notice Update threat level for a sector (called by ImmunoGrid nodes)
     * @param sector       City sector name
     * @param threatScore  0-10000 threat score
     * @param attackCount  Attacks in last 24h
     * @param attackType   Latest attack type (for critical alerts)
     */
    function updateSectorThreat(
        string calldata sector,
        uint256         threatScore,
        uint256         attackCount,
        string calldata attackType
    ) external onlyAuthorized {
        require(threatScore <= 10000, "Oracle: Score out of range");

        ThreatLevel storage tl = sectorThreat[sector];
        uint8 oldLevel = tl.level;

        // Compute threat level from score
        uint8 newLevel;
        if      (threatScore == 0)      newLevel = 0;  // NONE
        else if (threatScore < 2500)    newLevel = 1;  // LOW
        else if (threatScore < 5000)    newLevel = 2;  // MEDIUM
        else if (threatScore < 7500)    newLevel = 3;  // HIGH
        else                            newLevel = 4;  // CRITICAL

        tl.level              = newLevel;
        tl.score              = threatScore;
        tl.lastUpdated        = block.timestamp;
        tl.attackCount24h     = attackCount;
        tl.underActiveAttack  = attackCount > 0;

        emit ThreatLevelUpdated(sector, oldLevel, newLevel, threatScore, block.timestamp);

        // Critical alert for level 4
        if (newLevel == 4) {
            emit CriticalAlert(sector, attackType, block.timestamp);
        }

        // Update global threat score (average of all sectors)
        _updateGlobalScore();
    }

    /**
     * @notice Update device trust score from quantum fingerprint result
     * @param deviceId    Device identifier
     * @param trustScore  0-10000 trust score
     * @param fpFidelity  Quantum fingerprint fidelity × 10000
     */
    function updateDeviceTrust(
        string calldata deviceId,
        uint256         trustScore,
        uint256         fpFidelity
    ) external onlyAuthorized {
        require(trustScore  <= 10000, "Oracle: Trust out of range");
        require(fpFidelity  <= 10000, "Oracle: Fidelity out of range");

        bool isTrusted = trustScore >= 9200;  // 92% threshold

        deviceTrust[deviceId] = DeviceTrust({
            deviceId:     deviceId,
            trustScore:   trustScore,
            isTrusted:    isTrusted,
            lastVerified: block.timestamp,
            fpFidelity:   fpFidelity
        });

        emit DeviceTrustUpdated(deviceId, trustScore, isTrusted, fpFidelity, block.timestamp);
    }

    // ── Query Functions ───────────────────────────────────────────────────────

    /**
     * @notice Check if a sector is safe (threat level ≤ LOW)
     * @return safe         True if sector is safe
     * @return threatLevel  Current threat level (0-4)
     * @return score        Current threat score (0-10000)
     */
    function isSectorSafe(string calldata sector)
        external
        view
        returns (bool safe, uint8 threatLevel, uint256 score)
    {
        ThreatLevel memory tl = sectorThreat[sector];
        return (tl.level <= 1, tl.level, tl.score);
    }

    /**
     * @notice Check if a device is trusted
     * @return trusted    True if device trust score ≥ 9200
     * @return score      Trust score (0-10000)
     * @return fidelity   Quantum fingerprint fidelity × 10000
     */
    function isDeviceTrusted(string calldata deviceId)
        external
        view
        returns (bool trusted, uint256 score, uint256 fidelity)
    {
        DeviceTrust memory dt = deviceTrust[deviceId];
        if (dt.lastVerified == 0) {
            return (false, 0, 0);  // Unknown device = untrusted
        }
        return (dt.isTrusted, dt.trustScore, dt.fpFidelity);
    }

    /**
     * @notice Get global system threat level
     * @return score  0-10000 (0=fully safe, 10000=critical)
     * @return level  0=NONE 1=LOW 2=MEDIUM 3=HIGH 4=CRITICAL
     */
    function getGlobalThreat() external view returns (uint256 score, uint8 level) {
        uint8 lvl;
        if      (globalThreatScore == 0)    lvl = 0;
        else if (globalThreatScore < 2500)  lvl = 1;
        else if (globalThreatScore < 5000)  lvl = 2;
        else if (globalThreatScore < 7500)  lvl = 3;
        else                                lvl = 4;
        return (globalThreatScore, lvl);
    }

    /**
     * @notice Get all sector threat levels at once
     */
    function getAllSectorThreats()
        external
        view
        returns (
            string[] memory sectors,
            uint8[]  memory levels,
            uint256[] memory scores,
            bool[]   memory underAttack
        )
    {
        string[8] memory sectorNames = [
            "traffic","hospital","water","power",
            "surveillance","metro","airport","government"
        ];
        uint256 n = sectorNames.length;
        sectors    = new string[](n);
        levels     = new uint8[](n);
        scores     = new uint256[](n);
        underAttack = new bool[](n);

        for (uint256 i = 0; i < n; i++) {
            ThreatLevel memory tl = sectorThreat[sectorNames[i]];
            sectors[i]    = sectorNames[i];
            levels[i]     = tl.level;
            scores[i]     = tl.score;
            underAttack[i]= tl.underActiveAttack;
        }
    }

    // ── Subscription ─────────────────────────────────────────────────────────

    /**
     * @notice Subscribe to oracle updates (other contracts or wallets)
     */
    function subscribe() external {
        if (!subscribers[msg.sender]) {
            subscribers[msg.sender] = true;
            subscriberList.push(msg.sender);
            emit NewSubscriber(msg.sender, block.timestamp);
        }
    }

    function unsubscribe() external {
        subscribers[msg.sender] = false;
    }

    // ── Internal ──────────────────────────────────────────────────────────────

    function _updateGlobalScore() internal {
        string[8] memory sectorNames = [
            "traffic","hospital","water","power",
            "surveillance","metro","airport","government"
        ];

        uint256 total = 0;
        for (uint256 i = 0; i < sectorNames.length; i++) {
            total += sectorThreat[sectorNames[i]].score;
        }

        uint256 oldScore = globalThreatScore;
        globalThreatScore = total / sectorNames.length;
        lastGlobalUpdate  = block.timestamp;

        if (globalThreatScore != oldScore) {
            emit GlobalThreatUpdated(oldScore, globalThreatScore, block.timestamp);
        }
    }

    // ── Admin ─────────────────────────────────────────────────────────────────

    function setImmunoGridContract(address addr) external onlyOwner {
        immunoGridContract = IImmunoGrid(addr);
    }

    function resetSector(string calldata sector) external onlyOwner {
        sectorThreat[sector] = ThreatLevel({
            level: 0, score: 0,
            lastUpdated: block.timestamp,
            attackCount24h: 0,
            underActiveAttack: false
        });
        _updateGlobalScore();
    }

    function getSubscriberCount() external view returns (uint256) {
        return subscriberList.length;
    }
}
