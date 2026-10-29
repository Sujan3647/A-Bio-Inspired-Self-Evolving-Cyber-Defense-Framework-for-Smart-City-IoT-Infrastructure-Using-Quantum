// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImmunoGrid Access Control
 * @notice Role-Based Access Control (RBAC) for smart city departments
 * @dev Mirrors the 13 government roles in the backend RBAC system
 *      on-chain, so only authorized wallets can call sensitive functions.
 *
 * Roles:
 *   SUPER_ADMIN              — Full access
 *   NATIONAL_SECURITY_OFFICER— Read all, trigger morphogenesis
 *   CITY_IT_MANAGER          — Read all sectors
 *   TRAFFIC_MINISTRY         — Traffic sector only
 *   HEALTH_MINISTRY          — Hospital sector only
 *   WATER_AUTHORITY          — Water sector only
 *   ENERGY_MINISTRY          — Power sector only
 *   BLOCKCHAIN_AUDITOR       — Read-only audit access
 *   AI_ML_ENGINEER           — FL model registry access
 *   QUANTUM_ANALYST          — Key registry + FP stats
 *   DEVOPS_ENGINEER          — Infrastructure monitoring
 *   FIELD_TECHNICIAN         — Device-level read only
 *   GOVERNMENT_AUDITOR       — Read-only compliance
 */

contract ImmunoGridAccess {

    // ── Roles ─────────────────────────────────────────────────────────────────

    bytes32 public constant SUPER_ADMIN               = keccak256("SUPER_ADMIN");
    bytes32 public constant NATIONAL_SECURITY_OFFICER = keccak256("NATIONAL_SECURITY_OFFICER");
    bytes32 public constant CITY_IT_MANAGER           = keccak256("CITY_IT_MANAGER");
    bytes32 public constant TRAFFIC_MINISTRY          = keccak256("TRAFFIC_MINISTRY");
    bytes32 public constant HEALTH_MINISTRY           = keccak256("HEALTH_MINISTRY");
    bytes32 public constant WATER_AUTHORITY           = keccak256("WATER_AUTHORITY");
    bytes32 public constant ENERGY_MINISTRY           = keccak256("ENERGY_MINISTRY");
    bytes32 public constant BLOCKCHAIN_AUDITOR        = keccak256("BLOCKCHAIN_AUDITOR");
    bytes32 public constant AI_ML_ENGINEER            = keccak256("AI_ML_ENGINEER");
    bytes32 public constant QUANTUM_ANALYST           = keccak256("QUANTUM_ANALYST");
    bytes32 public constant DEVOPS_ENGINEER           = keccak256("DEVOPS_ENGINEER");
    bytes32 public constant FIELD_TECHNICIAN          = keccak256("FIELD_TECHNICIAN");
    bytes32 public constant GOVERNMENT_AUDITOR        = keccak256("GOVERNMENT_AUDITOR");

    // ── State ─────────────────────────────────────────────────────────────────

    address public owner;

    // role => (address => hasRole)
    mapping(bytes32 => mapping(address => bool)) private _roles;

    // address => their primary role
    mapping(address => bytes32) public primaryRole;

    // address => ministry/department
    mapping(address => string) public userMinistry;

    // ── Events ────────────────────────────────────────────────────────────────

    event RoleGranted(bytes32 indexed role, address indexed account, address indexed grantor);
    event RoleRevoked(bytes32 indexed role, address indexed account, address indexed revoker);
    event UserRegistered(address indexed account, bytes32 role, string ministry);

    // ── Modifiers ─────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Access: Not owner");
        _;
    }

    modifier onlyRole(bytes32 role) {
        require(hasRole(role, msg.sender), "Access: Missing required role");
        _;
    }

    modifier onlyAdminRoles() {
        require(
            hasRole(SUPER_ADMIN, msg.sender) ||
            hasRole(NATIONAL_SECURITY_OFFICER, msg.sender) ||
            hasRole(CITY_IT_MANAGER, msg.sender),
            "Access: Admin role required"
        );
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        _roles[SUPER_ADMIN][msg.sender] = true;
        primaryRole[msg.sender] = SUPER_ADMIN;
        userMinistry[msg.sender] = "National Cybersecurity Authority";
        emit RoleGranted(SUPER_ADMIN, msg.sender, msg.sender);
        emit UserRegistered(msg.sender, SUPER_ADMIN, "National Cybersecurity Authority");
    }

    // ── Role Management ───────────────────────────────────────────────────────

    /**
     * @notice Check if an address has a specific role
     */
    function hasRole(bytes32 role, address account) public view returns (bool) {
        return _roles[role][account];
    }

    /**
     * @notice Grant a role to an address
     */
    function grantRole(
        bytes32         role,
        address         account,
        string calldata ministry
    ) external onlyOwner {
        require(account != address(0), "Access: Zero address");
        _roles[role][account]  = true;
        primaryRole[account]   = role;
        userMinistry[account]  = ministry;
        emit RoleGranted(role, account, msg.sender);
        emit UserRegistered(account, role, ministry);
    }

    /**
     * @notice Revoke a role from an address
     */
    function revokeRole(bytes32 role, address account) external onlyOwner {
        _roles[role][account] = false;
        emit RoleRevoked(role, account, msg.sender);
    }

    /**
     * @notice Check if an address can write attack records
     * @dev Only SUPER_ADMIN, NATIONAL_SECURITY_OFFICER, and CITY_IT_MANAGER
     */
    function canRecordAttack(address account) external view returns (bool) {
        return (
            hasRole(SUPER_ADMIN, account) ||
            hasRole(NATIONAL_SECURITY_OFFICER, account) ||
            hasRole(CITY_IT_MANAGER, account)
        );
    }

    /**
     * @notice Check if an address can read a specific sector
     */
    function canReadSector(address account, string calldata sector) external view returns (bool) {
        // Admin roles can read all sectors
        if (hasRole(SUPER_ADMIN, account) ||
            hasRole(NATIONAL_SECURITY_OFFICER, account) ||
            hasRole(CITY_IT_MANAGER, account) ||
            hasRole(GOVERNMENT_AUDITOR, account) ||
            hasRole(BLOCKCHAIN_AUDITOR, account)) {
            return true;
        }

        bytes32 sectorHash = keccak256(bytes(sector));

        if (sectorHash == keccak256("traffic"))     return hasRole(TRAFFIC_MINISTRY,  account);
        if (sectorHash == keccak256("hospital"))    return hasRole(HEALTH_MINISTRY,   account);
        if (sectorHash == keccak256("water"))       return hasRole(WATER_AUTHORITY,   account);
        if (sectorHash == keccak256("power"))       return hasRole(ENERGY_MINISTRY,   account);

        return false;
    }

    /**
     * @notice Check if an address can trigger morphogenesis
     */
    function canTriggerMorphogenesis(address account) external view returns (bool) {
        return (
            hasRole(SUPER_ADMIN, account) ||
            hasRole(NATIONAL_SECURITY_OFFICER, account)
        );
    }

    /**
     * @notice Get role name as string (for display)
     */
    function getRoleName(bytes32 role) external pure returns (string memory) {
        if (role == SUPER_ADMIN)               return "Super Admin";
        if (role == NATIONAL_SECURITY_OFFICER) return "National Security Officer";
        if (role == CITY_IT_MANAGER)           return "City IT Manager";
        if (role == TRAFFIC_MINISTRY)          return "Traffic Ministry";
        if (role == HEALTH_MINISTRY)           return "Health Ministry";
        if (role == WATER_AUTHORITY)           return "Water Authority";
        if (role == ENERGY_MINISTRY)           return "Energy Ministry";
        if (role == BLOCKCHAIN_AUDITOR)        return "Blockchain Auditor";
        if (role == AI_ML_ENGINEER)            return "AI/ML Engineer";
        if (role == QUANTUM_ANALYST)           return "Quantum Analyst";
        if (role == DEVOPS_ENGINEER)           return "DevOps Engineer";
        if (role == FIELD_TECHNICIAN)          return "Field Technician";
        if (role == GOVERNMENT_AUDITOR)        return "Government Auditor";
        return "Unknown Role";
    }

    /**
     * @notice Get all info for an address
     */
    function getUserInfo(address account) external view returns (
        bytes32 role,
        string memory roleName,
        string memory ministry,
        bool   canRecord,
        bool   canMorph
    ) {
        role     = primaryRole[account];
        ministry = userMinistry[account];
        canRecord = (
            hasRole(SUPER_ADMIN, account) ||
            hasRole(NATIONAL_SECURITY_OFFICER, account) ||
            hasRole(CITY_IT_MANAGER, account)
        );
        canMorph = (
            hasRole(SUPER_ADMIN, account) ||
            hasRole(NATIONAL_SECURITY_OFFICER, account)
        );

        // Build role name inline
        if (role == SUPER_ADMIN)               roleName = "Super Admin";
        else if (role == NATIONAL_SECURITY_OFFICER) roleName = "National Security Officer";
        else if (role == CITY_IT_MANAGER)      roleName = "City IT Manager";
        else if (role == BLOCKCHAIN_AUDITOR)   roleName = "Blockchain Auditor";
        else if (role == GOVERNMENT_AUDITOR)   roleName = "Government Auditor";
        else                                   roleName = "Government Officer";
    }
}
