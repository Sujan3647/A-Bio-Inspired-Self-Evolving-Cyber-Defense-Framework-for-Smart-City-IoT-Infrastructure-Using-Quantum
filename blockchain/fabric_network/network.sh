#!/bin/bash
# ImmunoGrid — Hyperledger Fabric Network Management Script
#
# Usage:
#   ./network.sh up          Start the network
#   ./network.sh down        Stop and clean up
#   ./network.sh generate    Generate crypto material
#   ./network.sh createChannel   Create the immunogrid channel
#   ./network.sh deployCC    Deploy ImmunoGrid chaincode
#   ./network.sh status      Show network status

set -e

CHANNEL_NAME="immunogrid-channel"
CHAINCODE_NAME="immunogrid"
CHAINCODE_VERSION="1.0"
CHAINCODE_PATH="./chaincode"
ORDERER_CA="./crypto-config/ordererOrganizations/immunogrid.gov/orderers/orderer.immunogrid.gov/msp/tlscacerts/tlsca.immunogrid.gov-cert.pem"

printHeader() {
    echo "╔══════════════════════════════════════════════╗"
    echo "║       ImmunoGrid — Fabric Network            ║"
    echo "╚══════════════════════════════════════════════╝"
}

generateCrypto() {
    echo "🔑 Generating crypto material..."
    cryptogen generate --config=./crypto-config.yaml
    echo "✅ Crypto material generated"
}

generateGenesisBlock() {
    echo "📦 Generating genesis block..."
    mkdir -p channel-artifacts
    configtxgen -profile ImmunoGridOrdererGenesis \
        -channelID system-channel \
        -outputBlock ./channel-artifacts/genesis.block
    echo "✅ Genesis block created"
}

generateChannelTx() {
    echo "📄 Generating channel transaction..."
    configtxgen -profile ImmunoGridChannel \
        -outputCreateChannelTx ./channel-artifacts/channel.tx \
        -channelID $CHANNEL_NAME
    echo "✅ Channel transaction created"
}

networkUp() {
    printHeader
    echo "🚀 Starting ImmunoGrid Fabric Network..."
    generateCrypto
    generateGenesisBlock
    generateChannelTx
    docker-compose up -d
    echo ""
    echo "✅ Network started. Services running:"
    docker-compose ps
}

networkDown() {
    echo "⏹️  Stopping ImmunoGrid Fabric Network..."
    docker-compose down --volumes --remove-orphans
    docker rm -f $(docker ps -aq --filter "name=dev-peer") 2>/dev/null || true
    docker rmi -f $(docker images | grep "^dev-peer" | awk '{print $3}') 2>/dev/null || true
    rm -rf channel-artifacts/ crypto-config/
    echo "✅ Network stopped and cleaned"
}

createChannel() {
    echo "📺 Creating channel: $CHANNEL_NAME..."
    peer channel create \
        -o orderer.immunogrid.gov:7050 \
        -c $CHANNEL_NAME \
        -f ./channel-artifacts/channel.tx \
        --tls --cafile $ORDERER_CA
    echo "✅ Channel created"

    echo "🤝 Joining peers to channel..."
    peer channel join -b ${CHANNEL_NAME}.block
    echo "✅ Peers joined channel"
}

deployChaincode() {
    echo "📦 Packaging chaincode..."
    peer lifecycle chaincode package ${CHAINCODE_NAME}.tar.gz \
        --path $CHAINCODE_PATH \
        --lang golang \
        --label ${CHAINCODE_NAME}_${CHAINCODE_VERSION}

    echo "📤 Installing chaincode on all peers..."
    peer lifecycle chaincode install ${CHAINCODE_NAME}.tar.gz

    echo "✅ Chaincode installed. Approve and commit next."
    echo "Run: peer lifecycle chaincode approveformyorg ..."
    echo "Run: peer lifecycle chaincode commit ..."
}

networkStatus() {
    echo "📊 Network Status:"
    docker-compose ps
    echo ""
    echo "📋 Running containers:"
    docker ps --filter "name=immunogrid" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

case "$1" in
    up)           networkUp          ;;
    down)         networkDown        ;;
    generate)     generateCrypto; generateGenesisBlock; generateChannelTx ;;
    createChannel) createChannel    ;;
    deployCC)     deployChaincode   ;;
    status)       networkStatus     ;;
    *)
        printHeader
        echo "Usage: $0 {up|down|generate|createChannel|deployCC|status}"
        exit 1
        ;;
esac
