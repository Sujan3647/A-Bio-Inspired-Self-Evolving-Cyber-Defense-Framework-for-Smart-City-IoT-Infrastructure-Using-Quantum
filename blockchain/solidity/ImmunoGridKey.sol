// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImmunoGrid Key Registry
 * @notice On-chain PQC public key registry for IoT devices
 * @dev Stores Kyber-512 and Dilithium-2 public key hashes for all devices.
 *      Devices register their public key hash on-chain.
 *      Any node can verify a device's key is the registered one.
 *      Key rotation is recorded with full audit trail.
 */

contract ImmunoGridKeyRegistry {

    // ── Structs ───────────────────────────────────────────────────────────────

    struct DeviceKey {
        bytes32  kemKeyHash;       // SHA-256 of Kyber-512 public key
        bytes32  sigKeyHash;       // SHA-256 of Dilithium-2 public key
        uint256  registeredAt;
        uint256  expiresAt;
        uint256  rotationCount;
        bool     isActive;
        address  registeredBy;
    }

    struct KeyRotationEvent {
        string   deviceId;
        bytes32  oldKemHash;
        bytes32  newKemHash;
        bytes32  oldSigHash;
        bytes32  newSigHash;
        uint256  timestamp;
        string   reason;
    }

    // ── State ─────────────────────────────────────────────────────────────────

    address public owner;
    uint256 public constant KEY_VALIDITY_SECONDS = 90 days;

    mapping(string => DeviceKey)       public deviceKeys;      // deviceId => keys
    mapping(string => bool)            public registeredDevices;
    KeyRotationEvent[]                 public rotationHistory;
    string[]                           public deviceList;

    // ── Events ────────────────────────────────────────────────────────────────

    event KeyRegistered(
        string  indexed deviceId,
        bytes32 kemKeyHash,
        bytes32 sigKeyHash,
        uint256 expiresAt
    );

    event KeyRotated(
        string  indexed deviceId,
        bytes32 newKemHash,
        bytes32 newSigHash,
        string  reason,
        uint256 timestamp
    );

    event KeyRevoked(
        string  indexed deviceId,
        string  reason,
        uint256 timestamp
    );

    event KeyExpiring(
        string  indexed deviceId,
        uint256 expiresAt,
        uint256 daysRemaining
    );

    // ── Modifier ─────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "KeyRegistry: Not owner");
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
    }

    // ── Core Functions ────────────────────────────────────────────────────────

    /**
     * @notice Register a new IoT device with its PQC public keys
     * @param deviceId    Unique device identifier
     * @param kemKeyHash  SHA-256 hash of Kyber-512 public key
     * @param sigKeyHash  SHA-256 hash of Dilithium-2 public key
     */
    function registerDevice(
        string calldata deviceId,
        bytes32         kemKeyHash,
        bytes32         sigKeyHash
    ) external onlyOwner {
        require(!registeredDevices[deviceId], "KeyRegistry: Device already registered");
        require(kemKeyHash != bytes32(0), "KeyRegistry: Invalid KEM key hash");
        require(sigKeyHash != bytes32(0), "KeyRegistry: Invalid sig key hash");

        uint256 expiresAt = block.timestamp + KEY_VALIDITY_SECONDS;

        deviceKeys[deviceId] = DeviceKey({
            kemKeyHash:     kemKeyHash,
            sigKeyHash:     sigKeyHash,
            registeredAt:   block.timestamp,
            expiresAt:      expiresAt,
            rotationCount:  0,
            isActive:       true,
            registeredBy:   msg.sender
        });

        registeredDevices[deviceId] = true;
        deviceList.push(deviceId);

        emit KeyRegistered(deviceId, kemKeyHash, sigKeyHash, expiresAt);
    }

    /**
     * @notice Rotate keys for a device (scheduled or emergency)
     * @param deviceId    Device ID
     * @param newKemHash  New Kyber-512 public key hash
     * @param newSigHash  New Dilithium-2 public key hash
     * @param reason      Rotation reason ("scheduled" or "emergency")
     */
    function rotateKey(
        string  calldata deviceId,
        bytes32          newKemHash,
        bytes32          newSigHash,
        string  calldata reason
    ) external onlyOwner {
        require(registeredDevices[deviceId], "KeyRegistry: Device not found");
        require(newKemHash != bytes32(0), "KeyRegistry: Invalid new KEM hash");
        require(newSigHash != bytes32(0), "KeyRegistry: Invalid new sig hash");

        DeviceKey storage dk = deviceKeys[deviceId];

        // Save rotation history
        rotationHistory.push(KeyRotationEvent({
            deviceId:   deviceId,
            oldKemHash: dk.kemKeyHash,
            newKemHash: newKemHash,
            oldSigHash: dk.sigKeyHash,
            newSigHash: newSigHash,
            timestamp:  block.timestamp,
            reason:     reason
        }));

        // Update keys
        dk.kemKeyHash    = newKemHash;
        dk.sigKeyHash    = newSigHash;
        dk.expiresAt     = block.timestamp + KEY_VALIDITY_SECONDS;
        dk.rotationCount++;
        dk.isActive      = true;

        emit KeyRotated(deviceId, newKemHash, newSigHash, reason, block.timestamp);
    }

    /**
     * @notice Revoke a device's keys (on compromise)
     */
    function revokeKey(
        string calldata deviceId,
        string calldata reason
    ) external onlyOwner {
        require(registeredDevices[deviceId], "KeyRegistry: Device not found");
        deviceKeys[deviceId].isActive = false;
        emit KeyRevoked(deviceId, reason, block.timestamp);
    }

    /**
     * @notice Verify a device's current key hash
     * @param deviceId    Device to verify
     * @param kemKeyHash  Presented KEM key hash
     * @param sigKeyHash  Presented sig key hash
     * @return valid      True if keys match and are not expired/revoked
     */
    function verifyKey(
        string  calldata deviceId,
        bytes32          kemKeyHash,
        bytes32          sigKeyHash
    ) external view returns (bool valid, string memory reason) {
        if (!registeredDevices[deviceId]) {
            return (false, "Device not registered");
        }

        DeviceKey memory dk = deviceKeys[deviceId];

        if (!dk.isActive) {
            return (false, "Key revoked");
        }

        if (block.timestamp > dk.expiresAt) {
            return (false, "Key expired");
        }

        if (dk.kemKeyHash != kemKeyHash) {
            return (false, "KEM key mismatch — possible IMPOSTOR");
        }

        if (dk.sigKeyHash != sigKeyHash) {
            return (false, "Signature key mismatch");
        }

        return (true, "Valid");
    }

    /**
     * @notice Check if a device's key is expiring within N days
     */
    function isKeyExpiringSoon(
        string calldata deviceId,
        uint256 warningDays
    ) external view returns (bool expiring, uint256 daysLeft) {
        if (!registeredDevices[deviceId]) return (false, 0);

        DeviceKey memory dk = deviceKeys[deviceId];
        uint256 warningSeconds = warningDays * 1 days;

        if (block.timestamp + warningSeconds >= dk.expiresAt) {
            uint256 secsLeft = dk.expiresAt > block.timestamp
                ? dk.expiresAt - block.timestamp : 0;
            return (true, secsLeft / 1 days);
        }
        return (false, (dk.expiresAt - block.timestamp) / 1 days);
    }

    /**
     * @notice Bulk register multiple devices
     */
    function bulkRegister(
        string[]  calldata deviceIds,
        bytes32[] calldata kemHashes,
        bytes32[] calldata sigHashes
    ) external onlyOwner {
        require(deviceIds.length == kemHashes.length, "Length mismatch");
        require(deviceIds.length == sigHashes.length, "Length mismatch");

        for (uint256 i = 0; i < deviceIds.length; i++) {
            if (!registeredDevices[deviceIds[i]]) {
                uint256 expiresAt = block.timestamp + KEY_VALIDITY_SECONDS;
                deviceKeys[deviceIds[i]] = DeviceKey({
                    kemKeyHash:    kemHashes[i],
                    sigKeyHash:    sigHashes[i],
                    registeredAt:  block.timestamp,
                    expiresAt:     expiresAt,
                    rotationCount: 0,
                    isActive:      true,
                    registeredBy:  msg.sender
                });
                registeredDevices[deviceIds[i]] = true;
                deviceList.push(deviceIds[i]);
                emit KeyRegistered(deviceIds[i], kemHashes[i], sigHashes[i], expiresAt);
            }
        }
    }

    /**
     * @notice Get total registered devices count
     */
    function getDeviceCount() external view returns (uint256) {
        return deviceList.length;
    }

    /**
     * @notice Get rotation history count
     */
    function getRotationCount() external view returns (uint256) {
        return rotationHistory.length;
    }
}
