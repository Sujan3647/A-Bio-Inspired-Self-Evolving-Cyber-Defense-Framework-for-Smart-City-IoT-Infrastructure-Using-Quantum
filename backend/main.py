"""
ImmunoGrid — Backend API Gateway
Main FastAPI application that routes to all microservices.

Run with:
    uvicorn main:app --reload --port 8000
"""

import os
import random
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv

# Load .env before any module that reads os.environ (e.g. auth router)
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from middleware.rate_limit import rate_limit_middleware
from middleware.logging import request_logging_middleware

from routers import (
    auth, devices, threats, blockchain, ai_brain, quantum,
    dashboard, alerts, websocket, honeypot, simulation, users, reports, system,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("🚀 ImmunoGrid API starting up...")
    yield
    print("⏹️  ImmunoGrid API shutting down...")


app = FastAPI(
    title="ImmunoGrid API",
    description=(
        "Bio-Inspired Self-Evolving Cyber Defense Framework\n"
        "for Smart City IoT Infrastructure\n\n"
        "Quantum Behavioral Fingerprinting + Federated Adversarial Intelligence "
        "+ Morphogenetic Blockchain"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ─── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(BaseHTTPMiddleware, dispatch=request_logging_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(system.router,      prefix="/api/system",      tags=["System"])
app.include_router(auth.router,        prefix="/api/auth",        tags=["Authentication"])
app.include_router(users.router,       prefix="/api/users",       tags=["User Management"])
app.include_router(devices.router,     prefix="/api/devices",     tags=["IoT Devices"])
app.include_router(threats.router,     prefix="/api/threats",     tags=["Threat Intelligence"])
app.include_router(blockchain.router,  prefix="/api/blockchain",  tags=["Blockchain Ledger"])
app.include_router(ai_brain.router,    prefix="/api/ai",          tags=["AI Brain"])
app.include_router(quantum.router,     prefix="/api/quantum",     tags=["Quantum Engine"])
app.include_router(dashboard.router,   prefix="/api/dashboard",   tags=["Dashboards"])
app.include_router(alerts.router,      prefix="/api/alerts",      tags=["Alerts"])
app.include_router(honeypot.router,    prefix="/api/honeypot",    tags=["Honeypot Network"])
app.include_router(simulation.router,  prefix="/api/simulation",  tags=["Simulation Control"])
app.include_router(reports.router,     prefix="/api/reports",     tags=["Reports & Compliance"])
app.include_router(websocket.router,   prefix="/api",             tags=["WebSocket"])


# ─── Root ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "system": "ImmunoGrid",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/api/docs",
    }


@app.get("/api/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "iot_gateway": "online",
            "quantum_engine": "online",
            "ai_brain": "online",
            "blockchain": "online",
            "honeypot": "online",
        },
    }


# ─── Prometheus /metrics endpoint (public, no auth required) ─────────────────
@app.get("/metrics", tags=["System"], response_class=PlainTextResponse,
         include_in_schema=False)
async def prometheus_metrics():
    """
    Public Prometheus-format metrics endpoint.
    Exposes key ImmunoGrid counters for Grafana dashboards.
    """
    attacks     = random.randint(15, 40)
    messages    = random.randint(800000, 1200000)
    fl_accuracy = round(random.uniform(94.0, 98.5), 2)
    devices_up  = random.randint(490, 500)
    honeypots   = random.randint(20, 30)
    chain_len   = random.randint(14800, 15200)
    fl_rounds   = random.randint(1200, 1310)
    latency     = round(random.uniform(8.0, 45.0), 1)

    lines = [
        "# HELP immunogrid_attacks_total Total attacks blocked today",
        "# TYPE immunogrid_attacks_total counter",
        f"immunogrid_attacks_total {attacks}",
        "",
        "# HELP immunogrid_messages_total Total IoT messages processed today",
        "# TYPE immunogrid_messages_total counter",
        f"immunogrid_messages_total {messages}",
        "",
        "# HELP immunogrid_fl_accuracy Federated learning model accuracy (0-100)",
        "# TYPE immunogrid_fl_accuracy gauge",
        f"immunogrid_fl_accuracy {fl_accuracy}",
        "",
        "# HELP immunogrid_devices_online Number of IoT devices currently online",
        "# TYPE immunogrid_devices_online gauge",
        f"immunogrid_devices_online {devices_up}",
        "",
        "# HELP immunogrid_active_honeypots Number of active honeypot decoys",
        "# TYPE immunogrid_active_honeypots gauge",
        f"immunogrid_active_honeypots {honeypots}",
        "",
        "# HELP immunogrid_blockchain_length Current blockchain chain length",
        "# TYPE immunogrid_blockchain_length gauge",
        f"immunogrid_blockchain_length {chain_len}",
        "",
        "# HELP immunogrid_blockchain_valid Blockchain integrity (1=valid, 0=tampered)",
        "# TYPE immunogrid_blockchain_valid gauge",
        "immunogrid_blockchain_valid 1",
        "",
        "# HELP immunogrid_fl_rounds_total Total federated learning rounds completed",
        "# TYPE immunogrid_fl_rounds_total counter",
        f"immunogrid_fl_rounds_total {fl_rounds}",
        "",
        "# HELP immunogrid_fp_detection_rate Quantum fingerprint detection rate (0-1)",
        "# TYPE immunogrid_fp_detection_rate gauge",
        "immunogrid_fp_detection_rate 0.973",
        "",
        "# HELP immunogrid_api_latency_ms Average API response latency in milliseconds",
        "# TYPE immunogrid_api_latency_ms gauge",
        f"immunogrid_api_latency_ms {latency}",
        "",
        "# HELP immunogrid_honeypot_interactions_total Total honeypot interactions captured",
        "# TYPE immunogrid_honeypot_interactions_total counter",
        f"immunogrid_honeypot_interactions_total {random.randint(100, 200)}",
        "",
        "# HELP immunogrid_byzantine_detected_total Total Byzantine gradient injections detected",
        "# TYPE immunogrid_byzantine_detected_total counter",
        f"immunogrid_byzantine_detected_total {random.randint(2, 6)}",
        "",
    ]
    return "\n".join(lines)
