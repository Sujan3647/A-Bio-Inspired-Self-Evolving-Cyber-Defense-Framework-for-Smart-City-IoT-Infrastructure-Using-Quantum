require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },

  networks: {
    // Local Hardhat node (development)
    hardhat: {
      chainId: 31337,
    },

    // Local Ganache
    ganache: {
      url: "http://127.0.0.1:7545",
      accounts: {
        mnemonic: process.env.MNEMONIC || "test test test test test test test test test test test junk",
      },
    },

    // Ethereum Sepolia testnet
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "https://rpc.sepolia.org",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
    },

    // Polygon Mumbai testnet
    mumbai: {
      url: process.env.MUMBAI_RPC_URL || "https://rpc-mumbai.maticvigil.com",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 80001,
    },

    // Hyperledger Besu (private network)
    besu: {
      url: process.env.BESU_RPC_URL || "http://localhost:8545",
      accounts: process.env.BESU_PRIVATE_KEY ? [process.env.BESU_PRIVATE_KEY] : [],
      chainId: parseInt(process.env.BESU_CHAIN_ID || "1337"),
    },
  },

  etherscan: {
    apiKey: {
      sepolia: process.env.ETHERSCAN_API_KEY || "",
      polygonMumbai: process.env.POLYGONSCAN_API_KEY || "",
    },
  },

  gasReporter: {
    enabled: process.env.REPORT_GAS === "true",
    currency: "USD",
    coinmarketcap: process.env.COINMARKETCAP_API_KEY,
  },

  paths: {
    sources: "./",
    tests:   "./test",
    cache:   "./cache",
    artifacts: "./artifacts",
  },
};
