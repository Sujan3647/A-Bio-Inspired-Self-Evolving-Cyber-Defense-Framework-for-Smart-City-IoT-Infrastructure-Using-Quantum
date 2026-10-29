"""
ImmunoGrid — WebSocket Router
Real-time push of live events to the frontend dashboard.

Events pushed:
- New attack detected
- Blockchain block mined
- Device status changed
- Morphogenesis triggered
- AI brain training round completed
"""

import asyncio
import json
import random
from datetime import datetime
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages all active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        payload = json.dumps(message)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)

    async def send_to(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        await websocket.send_text(json.dumps(message))


manager = ConnectionManager()

# ── Event Types ───────────────────────────────────────────────────────────────

EVENT_TYPES = [
    "attack_detected",
    "block_mined",
    "device_status_changed",
    "morphogenesis_triggered",
    "honeypot_triggered",
    "ai_round_completed",
    "impostor_detected",
]

ATTACK_TYPES = ["spoofing", "ddos", "data_poisoning", "replay_attack", "mitm", "ransomware"]
SECTORS = ["traffic", "hospital", "water", "power", "surveillance"]
SEVERITIES = ["low", "medium", "high", "critical"]


async def _simulate_event_stream(websocket: WebSocket):
    """
    Simulate a live event stream for dashboard demonstration.
    In production, this receives events from the actual IoT/AI/Blockchain modules.
    """
    event_count = 0
    while True:
        await asyncio.sleep(random.uniform(1.5, 4.0))

        event_type = random.choice(EVENT_TYPES)
        event_count += 1

        if event_type == "attack_detected":
            event = {
                "type": "attack_detected",
                "data": {
                    "attack_id": f"ATK-{event_count:06d}",
                    "attack_type": random.choice(ATTACK_TYPES),
                    "severity": random.choice(SEVERITIES),
                    "sector": random.choice(SECTORS),
                    "device_id": f"device-{random.randint(1, 500):04d}",
                    "detected_by": random.choice(["quantum_fingerprint", "ai_brain", "honeypot"]),
                    "status": "mitigated",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        elif event_type == "block_mined":
            event = {
                "type": "block_mined",
                "data": {
                    "block_index": random.randint(14800, 14900),
                    "attack_records": random.randint(1, 5),
                    "morphogenesis_commands": random.randint(0, 3),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        elif event_type == "morphogenesis_triggered":
            event = {
                "type": "morphogenesis_triggered",
                "data": {
                    "action": random.choice([
                        "honeypots_spawned",
                        "sector_isolated",
                        "firewall_updated",
                        "fp_sensitivity_increased",
                        "device_quarantined",
                    ]),
                    "sector": random.choice(SECTORS),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        elif event_type == "impostor_detected":
            event = {
                "type": "impostor_detected",
                "data": {
                    "device_id": f"device-{random.randint(1, 500):04d}",
                    "fidelity_score": round(random.uniform(0.60, 0.89), 4),
                    "verdict": random.choice(["IMPOSTOR", "SUSPICIOUS"]),
                    "sector": random.choice(SECTORS),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        elif event_type == "ai_round_completed":
            event = {
                "type": "ai_round_completed",
                "data": {
                    "round": random.randint(1200, 1300),
                    "accuracy": round(random.uniform(96.0, 98.5), 2),
                    "loss": round(random.uniform(0.05, 0.15), 4),
                    "participants": random.randint(480, 500),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        elif event_type == "honeypot_triggered":
            event = {
                "type": "honeypot_triggered",
                "data": {
                    "honeypot_id": f"honeypot-{random.randint(1, 23):03d}",
                    "attacker_caught": True,
                    "attack_type": random.choice(ATTACK_TYPES),
                    "sector": random.choice(SECTORS),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        else:
            event = {
                "type": "device_status_changed",
                "data": {
                    "device_id": f"device-{random.randint(1, 500):04d}",
                    "old_status": "online",
                    "new_status": random.choice(["compromised", "quarantined", "online"]),
                    "sector": random.choice(SECTORS),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        event["event_id"] = event_count
        await manager.send_to(websocket, event)


# ── WebSocket Endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    Connect from React frontend:
        const ws = new WebSocket('ws://localhost:8000/api/ws/live')
    """
    await manager.connect(websocket)
    try:
        # Send connection confirmation
        await manager.send_to(websocket, {
            "type": "connected",
            "message": "ImmunoGrid live feed connected",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Start simulated event stream
        await _simulate_event_stream(websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception:
        manager.disconnect(websocket)


@router.websocket("/ws/sector/{sector}")
async def websocket_sector(websocket: WebSocket, sector: str):
    """
    Sector-specific WebSocket feed.
    Only sends events for the specified sector.
    """
    await manager.connect(websocket)
    try:
        await manager.send_to(websocket, {
            "type": "connected",
            "sector": sector,
            "message": f"ImmunoGrid {sector} sector feed connected",
            "timestamp": datetime.utcnow().isoformat(),
        })

        while True:
            await asyncio.sleep(random.uniform(2.0, 5.0))
            event = {
                "type": "sector_update",
                "sector": sector,
                "data": {
                    "devices_online": random.randint(80, 100),
                    "threats": random.randint(0, 3),
                    "fingerprint_rate": round(random.uniform(97.0, 100.0), 2),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }
            await manager.send_to(websocket, event)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
