/**
 * ImmunoGridAccess — Unit Tests
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ImmunoGridAccess — Role-Based Access Control", () => {

  let access, owner, user1, user2, auditor;

  const ROLES = {
    SUPER_ADMIN:               ethers.keccak256(ethers.toUtf8Bytes("SUPER_ADMIN")),
    NATIONAL_SECURITY_OFFICER: ethers.keccak256(ethers.toUtf8Bytes("NATIONAL_SECURITY_OFFICER")),
    CITY_IT_MANAGER:           ethers.keccak256(ethers.toUtf8Bytes("CITY_IT_MANAGER")),
    TRAFFIC_MINISTRY:          ethers.keccak256(ethers.toUtf8Bytes("TRAFFIC_MINISTRY")),
    HEALTH_MINISTRY:           ethers.keccak256(ethers.toUtf8Bytes("HEALTH_MINISTRY")),
    BLOCKCHAIN_AUDITOR:        ethers.keccak256(ethers.toUtf8Bytes("BLOCKCHAIN_AUDITOR")),
    GOVERNMENT_AUDITOR:        ethers.keccak256(ethers.toUtf8Bytes("GOVERNMENT_AUDITOR")),
    QUANTUM_ANALYST:           ethers.keccak256(ethers.toUtf8Bytes("QUANTUM_ANALYST")),
  };

  beforeEach(async () => {
    [owner, user1, user2, auditor] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ImmunoGridAccess");
    access = await Factory.deploy();
    await access.waitForDeployment();
  });

  describe("Deployment", () => {
    it("should give owner SUPER_ADMIN role", async () => {
      expect(await access.hasRole(ROLES.SUPER_ADMIN, owner.address)).to.be.true;
    });

    it("should set owner correctly", async () => {
      expect(await access.owner()).to.equal(owner.address);
    });
  });

  describe("grantRole", () => {
    it("should grant role to user", async () => {
      await access.grantRole(ROLES.TRAFFIC_MINISTRY, user1.address, "Ministry of Transport");
      expect(await access.hasRole(ROLES.TRAFFIC_MINISTRY, user1.address)).to.be.true;
    });

    it("should set primary role and ministry", async () => {
      await access.grantRole(ROLES.HEALTH_MINISTRY, user1.address, "Ministry of Health");
      expect(await access.primaryRole(user1.address)).to.equal(ROLES.HEALTH_MINISTRY);
      expect(await access.userMinistry(user1.address)).to.equal("Ministry of Health");
    });

    it("should emit RoleGranted event", async () => {
      await expect(
        access.grantRole(ROLES.BLOCKCHAIN_AUDITOR, user2.address, "Audit Office")
      ).to.emit(access, "RoleGranted");
    });

    it("should reject grant from non-owner", async () => {
      await expect(
        access.connect(user1).grantRole(ROLES.SUPER_ADMIN, user2.address, "Org")
      ).to.be.revertedWith("Access: Not owner");
    });
  });

  describe("revokeRole", () => {
    it("should revoke role", async () => {
      await access.grantRole(ROLES.TRAFFIC_MINISTRY, user1.address, "Transport");
      await access.revokeRole(ROLES.TRAFFIC_MINISTRY, user1.address);
      expect(await access.hasRole(ROLES.TRAFFIC_MINISTRY, user1.address)).to.be.false;
    });
  });

  describe("canReadSector", () => {
    it("admin should read all sectors", async () => {
      for (const sector of ["traffic","hospital","water","power","surveillance"]) {
        expect(await access.canReadSector(owner.address, sector)).to.be.true;
      }
    });

    it("traffic ministry reads only traffic sector", async () => {
      await access.grantRole(ROLES.TRAFFIC_MINISTRY, user1.address, "Transport");
      expect(await access.canReadSector(user1.address, "traffic")).to.be.true;
      expect(await access.canReadSector(user1.address, "hospital")).to.be.false;
      expect(await access.canReadSector(user1.address, "water")).to.be.false;
    });

    it("health ministry reads only hospital sector", async () => {
      await access.grantRole(ROLES.HEALTH_MINISTRY, user2.address, "Health");
      expect(await access.canReadSector(user2.address, "hospital")).to.be.true;
      expect(await access.canReadSector(user2.address, "traffic")).to.be.false;
    });

    it("government auditor reads all sectors", async () => {
      await access.grantRole(ROLES.GOVERNMENT_AUDITOR, auditor.address, "Audit");
      for (const s of ["traffic","hospital","water","power"]) {
        expect(await access.canReadSector(auditor.address, s)).to.be.true;
      }
    });
  });

  describe("canRecordAttack", () => {
    it("super admin can record attacks", async () => {
      expect(await access.canRecordAttack(owner.address)).to.be.true;
    });

    it("traffic ministry cannot record attacks", async () => {
      await access.grantRole(ROLES.TRAFFIC_MINISTRY, user1.address, "Transport");
      expect(await access.canRecordAttack(user1.address)).to.be.false;
    });

    it("city IT manager can record attacks", async () => {
      await access.grantRole(ROLES.CITY_IT_MANAGER, user1.address, "IT Dept");
      expect(await access.canRecordAttack(user1.address)).to.be.true;
    });
  });

  describe("canTriggerMorphogenesis", () => {
    it("super admin can trigger morphogenesis", async () => {
      expect(await access.canTriggerMorphogenesis(owner.address)).to.be.true;
    });

    it("city IT manager cannot trigger morphogenesis", async () => {
      await access.grantRole(ROLES.CITY_IT_MANAGER, user1.address, "IT");
      expect(await access.canTriggerMorphogenesis(user1.address)).to.be.false;
    });

    it("national security officer can trigger morphogenesis", async () => {
      await access.grantRole(ROLES.NATIONAL_SECURITY_OFFICER, user1.address, "NSO");
      expect(await access.canTriggerMorphogenesis(user1.address)).to.be.true;
    });
  });

  describe("getRoleName", () => {
    it("should return correct role names", async () => {
      const tests = [
        [ROLES.SUPER_ADMIN,               "Super Admin"],
        [ROLES.NATIONAL_SECURITY_OFFICER, "National Security Officer"],
        [ROLES.CITY_IT_MANAGER,           "City IT Manager"],
        [ROLES.BLOCKCHAIN_AUDITOR,        "Blockchain Auditor"],
        [ROLES.GOVERNMENT_AUDITOR,        "Government Auditor"],
      ];
      for (const [role, name] of tests) {
        expect(await access.getRoleName(role)).to.equal(name);
      }
    });
  });

  describe("getUserInfo", () => {
    it("should return complete user info", async () => {
      const [role, roleName, ministry, canRecord, canMorph] =
        await access.getUserInfo(owner.address);

      expect(role).to.equal(ROLES.SUPER_ADMIN);
      expect(roleName).to.equal("Super Admin");
      expect(ministry).to.equal("National Cybersecurity Authority");
      expect(canRecord).to.be.true;
      expect(canMorph).to.be.true;
    });
  });
});
