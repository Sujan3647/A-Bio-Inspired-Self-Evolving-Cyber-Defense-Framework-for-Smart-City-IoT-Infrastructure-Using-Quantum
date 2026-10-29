"""
ImmunoGrid — IoT Network Topology
Models the mesh network connecting all 500+ smart city devices.

Topology types:
- Star:  All devices connect directly to gateway (simple, single point of failure)
- Mesh:  Devices form peer-to-peer connections (resilient, complex)
- Hybrid: Sector-level star networks connected in a mesh (ImmunoGrid uses this)

The Morphogenetic Blockchain reshapes this topology after attacks:
- Isolate compromised sectors
- Create alternate routing paths
- Deploy honeypots at strategic network positions
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class NetworkNode:
    """A node in the IoT network topology."""
    node_id:    str
    node_type:  str          # "device", "gateway", "honeypot", "relay"
    sector:     str
    location:   str
    connections: List[str] = field(default_factory=list)   # Connected node IDs
    is_active:  bool = True
    is_isolated: bool = False
    hop_count:  int = 0      # Hops to gateway


@dataclass
class NetworkPath:
    """A routing path between two nodes."""
    source:      str
    destination: str
    hops:        List[str]
    latency_ms:  float
    is_secure:   bool
    path_hash:   str


class SmartCityNetworkTopology:
    """
    Models the hybrid mesh network topology of a smart city.
    Supports dynamic reshaping via morphogenesis.
    """

    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.gateway_id = "GATEWAY-CENTRAL"
        self.sector_gateways: Dict[str, str] = {}
        self.routing_table: Dict[str, str] = {}   # node_id → next_hop
        self.morphogenesis_events: int = 0

        # Create central gateway
        self._add_node(NetworkNode(
            node_id=self.gateway_id,
            node_type="gateway",
            sector="central",
            location="data-center",
        ))

        logger.info("network_topology_initialized")

    def _add_node(self, node: NetworkNode):
        self.nodes[node.node_id] = node

    def add_sector(self, sector_name: str, device_ids: List[str], locations: List[str]):
        """Add a sector with its devices and a sector gateway."""
        # Sector gateway
        gw_id = f"GW-{sector_name.upper()}"
        sector_gw = NetworkNode(
            node_id=gw_id,
            node_type="gateway",
            sector=sector_name,
            location=f"{sector_name}-gateway",
            connections=[self.gateway_id],
            hop_count=1,
        )
        self._add_node(sector_gw)
        self.sector_gateways[sector_name] = gw_id

        # Connect sector gateway to central
        self.nodes[self.gateway_id].connections.append(gw_id)

        # Add devices — star topology within sector
        for i, dev_id in enumerate(device_ids):
            location = locations[i % len(locations)]
            device_node = NetworkNode(
                node_id=dev_id,
                node_type="device",
                sector=sector_name,
                location=location,
                connections=[gw_id],
                hop_count=2,
            )
            self._add_node(device_node)
            sector_gw.connections.append(dev_id)

    def get_path(self, source_id: str, dest_id: str) -> Optional[NetworkPath]:
        """Find the routing path from source to destination."""
        import hashlib

        if source_id not in self.nodes or dest_id not in self.nodes:
            return None

        source = self.nodes[source_id]

        # Simple routing: device → sector_gateway → central_gateway → dest_sector_gateway → dest
        hops = [source_id]

        # Go up to sector gateway
        sector_gw = self.sector_gateways.get(source.sector)
        if sector_gw and sector_gw not in hops:
            hops.append(sector_gw)

        dest = self.nodes.get(dest_id)
        if dest:
            # Through central if crossing sectors
            if dest.sector != source.sector:
                hops.append(self.gateway_id)
                dest_gw = self.sector_gateways.get(dest.sector)
                if dest_gw:
                    hops.append(dest_gw)

        hops.append(dest_id)

        # Latency estimate
        latency_ms = len(hops) * random.uniform(1.5, 4.0)

        path_hash = hashlib.sha256("→".join(hops).encode()).hexdigest()[:16]

        return NetworkPath(
            source=source_id,
            destination=dest_id,
            hops=hops,
            latency_ms=round(latency_ms, 2),
            is_secure=all(self.nodes.get(h, NetworkNode("", "", "", "")).is_active for h in hops),
            path_hash=path_hash,
        )

    def isolate_sector(self, sector: str) -> List[str]:
        """Isolate a sector — disconnect from main network (morphogenesis)."""
        affected = []
        gw_id = self.sector_gateways.get(sector)
        if gw_id and gw_id in self.nodes:
            self.nodes[gw_id].is_isolated = True
            # Remove connection from central gateway
            if gw_id in self.nodes[self.gateway_id].connections:
                self.nodes[self.gateway_id].connections.remove(gw_id)
            affected.append(gw_id)

        for node in self.nodes.values():
            if node.sector == sector:
                node.is_isolated = True
                affected.append(node.node_id)

        self.morphogenesis_events += 1
        logger.warning("sector_isolated_network", sector=sector, nodes_affected=len(affected))
        return affected

    def restore_sector(self, sector: str) -> bool:
        """Restore an isolated sector to the network."""
        gw_id = self.sector_gateways.get(sector)
        if gw_id and gw_id in self.nodes:
            self.nodes[gw_id].is_isolated = False
            if gw_id not in self.nodes[self.gateway_id].connections:
                self.nodes[self.gateway_id].connections.append(gw_id)

        for node in self.nodes.values():
            if node.sector == sector:
                node.is_isolated = False

        logger.info("sector_restored_network", sector=sector)
        return True

    def add_honeypot_node(self, sector: str, mimics_device: str) -> NetworkNode:
        """Add a honeypot node to the network topology."""
        honeypot_id = f"HONEYPOT-{sector.upper()}-{random.randint(1000,9999)}"
        gw_id = self.sector_gateways.get(sector, self.gateway_id)

        hp_node = NetworkNode(
            node_id=honeypot_id,
            node_type="honeypot",
            sector=sector,
            location=f"honeypot-{sector}",
            connections=[gw_id],
            hop_count=2,
        )
        self._add_node(hp_node)
        if gw_id in self.nodes:
            self.nodes[gw_id].connections.append(honeypot_id)

        self.morphogenesis_events += 1
        logger.info("honeypot_added_to_topology", honeypot_id=honeypot_id, sector=sector)
        return hp_node

    def get_topology_stats(self) -> Dict[str, Any]:
        """Return network topology statistics."""
        total_nodes  = len(self.nodes)
        active       = sum(1 for n in self.nodes.values() if n.is_active and not n.is_isolated)
        isolated     = sum(1 for n in self.nodes.values() if n.is_isolated)
        honeypots    = sum(1 for n in self.nodes.values() if n.node_type == "honeypot")
        gateways     = sum(1 for n in self.nodes.values() if n.node_type == "gateway")
        avg_degree   = (
            sum(len(n.connections) for n in self.nodes.values()) / max(total_nodes, 1)
        )

        return {
            "total_nodes":         total_nodes,
            "active_nodes":        active,
            "isolated_nodes":      isolated,
            "honeypot_nodes":      honeypots,
            "gateway_nodes":       gateways,
            "sectors":             len(self.sector_gateways),
            "avg_connections":     round(avg_degree, 2),
            "morphogenesis_events": self.morphogenesis_events,
            "topology_type":       "hybrid_mesh_star",
        }
