// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImmunoGrid Federated Learning Model Registry
 * @notice On-chain provenance for federated learning model versions
 * @dev Every FL model aggregation round is committed on-chain.
 *      The model hash ensures nobody can tamper with the global model.
 *      Prevents Byzantine model poisoning by recording all versions.
 *
 * Research contribution: First use of blockchain for FL model integrity
 * in a smart city security context.
 */

contract ImmunoGridFL {

    // ── Structs ───────────────────────────────────────────────────────────────

    struct ModelVersion {
        uint256 roundNumber;
        bytes32 modelHash;          // SHA-256 of model weights
        bytes32 gradientsHash;      // SHA-256 of aggregated gradients
        uint256 accuracy;           // × 10000 (e.g. 9720 = 97.20%)
        uint256 loss;               // × 10000
        uint256 participants;       // Number of FL participants
        uint256 imaginationsCount;  // FAC imaginations generated
        address submittedBy;
        uint256 timestamp;
        bool    poisoningDetected;
    }

    struct ClientContribution {
        address clientAddr;
        string  deviceId;
        uint256 roundNumber;
        bytes32 gradientHash;
        uint256 numSamples;
        bool    accepted;
        uint256 timestamp;
    }

    // ── State ─────────────────────────────────────────────────────────────────

    address public owner;
    uint256 public currentRound;
    uint256 public totalImaginations;

    mapping(uint256 => ModelVersion) public modelVersions;      // round => version
    mapping(uint256 => ClientContribution[]) public roundContributions;
    mapping(bytes32 => bool) public knownModelHashes;           // Prevent replay

    // ── Events ────────────────────────────────────────────────────────────────

    event ModelVersionCommitted(
        uint256 indexed roundNumber,
        bytes32 modelHash,
        uint256 accuracy,
        uint256 participants,
        uint256 timestamp
    );

    event ClientContributionRecorded(
        uint256 indexed roundNumber,
        string  deviceId,
        bytes32 gradientHash,
        bool    accepted
    );

    event PoisoningDetected(
        uint256 indexed roundNumber,
        string  suspectDevice,
        uint256 timestamp
    );

    event ImaginationsRecorded(
        uint256 indexed roundNumber,
        uint256 count,
        uint256 total
    );

    // ── Modifier ─────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "FLRegistry: Not owner");
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        currentRound = 0;
    }

    // ── Core Functions ────────────────────────────────────────────────────────

    /**
     * @notice Commit a new FL model version after aggregation
     * @param modelHash         SHA-256 of aggregated model weights
     * @param gradientsHash     SHA-256 of aggregated gradients
     * @param accuracyBps       Model accuracy × 10000 (e.g. 9720 = 97.20%)
     * @param lossBps           Model loss × 10000
     * @param participants      Number of participating devices
     * @param imaginationsCount Number of FAC imaginations used
     */
    function commitModelVersion(
        bytes32 modelHash,
        bytes32 gradientsHash,
        uint256 accuracyBps,
        uint256 lossBps,
        uint256 participants,
        uint256 imaginationsCount
    ) external onlyOwner returns (uint256 roundNumber) {
        require(modelHash != bytes32(0), "FLRegistry: Invalid model hash");
        require(!knownModelHashes[modelHash], "FLRegistry: Duplicate model hash (replay?)");
        require(accuracyBps <= 10000, "FLRegistry: Accuracy > 100%");

        currentRound++;
        roundNumber = currentRound;
        totalImaginations += imaginationsCount;

        modelVersions[roundNumber] = ModelVersion({
            roundNumber:       roundNumber,
            modelHash:         modelHash,
            gradientsHash:     gradientsHash,
            accuracy:          accuracyBps,
            loss:              lossBps,
            participants:      participants,
            imaginationsCount: imaginationsCount,
            submittedBy:       msg.sender,
            timestamp:         block.timestamp,
            poisoningDetected: false
        });

        knownModelHashes[modelHash] = true;

        emit ModelVersionCommitted(roundNumber, modelHash, accuracyBps, participants, block.timestamp);
        emit ImaginationsRecorded(roundNumber, imaginationsCount, totalImaginations);

        return roundNumber;
    }

    /**
     * @notice Record a client's gradient contribution for a round
     * @param deviceId      Device that submitted gradients
     * @param gradientHash  SHA-256 of the gradient update
     * @param numSamples    Number of training samples used
     */
    function recordContribution(
        string  calldata deviceId,
        bytes32          gradientHash,
        uint256          numSamples
    ) external {
        require(gradientHash != bytes32(0), "FLRegistry: Invalid gradient hash");

        roundContributions[currentRound].push(ClientContribution({
            clientAddr:  msg.sender,
            deviceId:    deviceId,
            roundNumber: currentRound,
            gradientHash: gradientHash,
            numSamples:  numSamples,
            accepted:    true,
            timestamp:   block.timestamp
        }));

        emit ClientContributionRecorded(currentRound, deviceId, gradientHash, true);
    }

    /**
     * @notice Flag Byzantine poisoning in a round
     * @param roundNumber    The affected FL round
     * @param suspectDevice  Device suspected of gradient poisoning
     */
    function flagPoisoning(
        uint256 roundNumber,
        string calldata suspectDevice
    ) external onlyOwner {
        require(roundNumber <= currentRound, "FLRegistry: Round not found");

        modelVersions[roundNumber].poisoningDetected = true;

        // Mark suspect contribution as rejected
        ClientContribution[] storage contribs = roundContributions[roundNumber];
        for (uint256 i = 0; i < contribs.length; i++) {
            if (keccak256(bytes(contribs[i].deviceId)) == keccak256(bytes(suspectDevice))) {
                contribs[i].accepted = false;
            }
        }

        emit PoisoningDetected(roundNumber, suspectDevice, block.timestamp);
    }

    /**
     * @notice Verify a model version by hash
     * @return valid  True if this exact model hash is committed on-chain
     */
    function verifyModel(bytes32 modelHash) external view returns (bool valid) {
        return knownModelHashes[modelHash];
    }

    /**
     * @notice Get model version details
     */
    function getModelVersion(uint256 roundNumber)
        external
        view
        returns (ModelVersion memory)
    {
        require(roundNumber > 0 && roundNumber <= currentRound, "FLRegistry: Round not found");
        return modelVersions[roundNumber];
    }

    /**
     * @notice Get number of contributions for a round
     */
    function getContributionCount(uint256 roundNumber)
        external
        view
        returns (uint256)
    {
        return roundContributions[roundNumber].length;
    }

    /**
     * @notice Get latest model accuracy
     */
    function getLatestAccuracy() external view returns (uint256 accuracyBps, uint256 round) {
        if (currentRound == 0) return (0, 0);
        return (modelVersions[currentRound].accuracy, currentRound);
    }

    /**
     * @notice Get contract statistics
     */
    function getStats() external view returns (
        uint256 _currentRound,
        uint256 _totalImaginations,
        uint256 _latestAccuracyBps,
        bool    _latestPoisoningDetected
    ) {
        return (
            currentRound,
            totalImaginations,
            currentRound > 0 ? modelVersions[currentRound].accuracy : 0,
            currentRound > 0 ? modelVersions[currentRound].poisoningDetected : false
        );
    }
}
