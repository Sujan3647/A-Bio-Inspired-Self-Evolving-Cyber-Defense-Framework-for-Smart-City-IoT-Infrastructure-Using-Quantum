# ImmunoGrid — Backend API

> FastAPI microservices backend for the ImmunoGrid smart city defense platform.

---

## Overview

The backend provides **14 routers** covering 64+ endpoints across:
- Authentication & RBAC (13 government roles)
- IoT device management
- Threat intelligence
- Quantum engine operations
- AI Brain / Federated Learning
- Morphogenetic Blockchain
- Honeypot network
- Simulation control
- Reports & compliance
- Real-time WebSocket feed

---

## Structure

```
backend/
├── main.py                     FastAPI app + middleware registration
├── Dockerfile                  Container build
├── docker-compose.yml          Local dev stack
├── mosquitto.conf              MQTT broker config
│
├── routers/                    14 API routers (54+ endpoints)
│   ├── auth.py                 Login, JWT, logout
│   ├── users.py                User CRUD + role management
│   ├── devices.py              IoT device registry
│   ├── threats.py              Threat events feed
│   ├── blockchain.py           Ledger + morphogenesis
│   ├── quantum.py              Fingerprint engine + attack sim
│   ├── ai_brain.py             FAC stats + classification + XAI
│   ├── dashboard.py            Sector dashboards data
│   ├── honeypot.py             Decoy network management
│   ├── simulation.py           Virtual city control
│   ├── reports.py              Compliance & intelligence reports
│   ├── alerts.py               Security alerts feed
│   ├── system.py               System status + metrics
│   └── websocket.py            Live event WebSocket
│
├── models/                     Pydantic schemas
│   ├── user.py                 User + RBAC + 13 roles
│   ├── device.py               IoT device types + status
│   ├── threat.py               Attack types + severity
│   └── response.py             Standardized API responses
│
├── services/                   Business logic layer
│   ├── quantum_service.py      QBF engine + attack simulation
│   ├── ai_service.py           FL stats + classifier + XAI
│   ├── blockchain_service.py   Chain ops + topology + pattern check
│   ├── honeypot_service.py     Decoy spawn + intelligence
│   └── iot_service.py          Device management + simulation
│
├── middleware/
│   ├── rate_limit.py           100 req/min (10 for auth endpoints)
│   └── logging.py              Request/response structured logging
│
├── database/
│   ├── connection.py           PostgreSQL + MongoDB + Redis
│   ├── models.py               SQLAlchemy ORM models
│   ├── crud.py                 CRUD operations for all models
│   ├── alembic.ini             Migration config
│   └── migrations/             Alembic migration scripts
│       ├── 001_initial.py      Base schema (7 tables)
│       └── 002_add_honeypot.py Honeypot + intelligence tables
│
└── tests/
    └── test_backend_complete.py  64 API endpoint tests
```

---

## Quick Start

```bash
# Start backend (port 8000)
cd backend
uvicorn main:app --reload --port 8000

# View API docs
open http://localhost:8000/api/docs

# Run tests
python tests/test_backend_complete.py
# Expected: 64/64 PASS
```

---

## Demo Login Accounts

| Email | Password | Role |
|---|---|---|
| admin@immunogrid.gov | Admin@123 | Super Admin |
| security@immunogrid.gov | Security@123 | National Security Officer |
| traffic@immunogrid.gov | Traffic@123 | Traffic Ministry |
| hospital@immunogrid.gov | Health@123 | Health Ministry |
| water@immunogrid.gov | Water@123 | Water Authority |
| energy@immunogrid.gov | Energy@123 | Energy Ministry |
| auditor@immunogrid.gov | Audit@123 | Government Auditor |
| quantum@immunogrid.gov | Quantum@123 | Quantum Analyst |
| devops@immunogrid.gov | DevOps@123 | DevOps Engineer |

---

## API Endpoints Summary

### Authentication (`/api/auth`)
- `POST /login` — JWT login
- `GET  /me` — Current user + permissions
- `POST /logout`
- `GET  /users` — List all users (Admin)

### User Management (`/api/users`)
- `GET  /` — List users
- `POST /` — Create user
- `PATCH /{id}` — Update user
- `DELETE /{id}` — Deactivate user
- `GET  /me/permissions` — My permissions
- `GET  /roles/all` — All 13 roles

### IoT Devices (`/api/devices`)
- `GET  /` — List devices (RBAC-filtered by sector)
- `GET  /stats` — Device counts by status/sector
- `GET  /{device_id}` — Single device detail

### Threat Intelligence (`/api/threats`)
- `GET  /` — Recent threats
- `GET  /summary` — Statistics
- `GET  /live` — Last 5 minutes

### Blockchain (`/api/blockchain`)
- `GET  /chain` — Block feed
- `GET  /stats` — Chain statistics
- `GET  /topology` — Morphogenesis network state
- `GET  /attacks` — Immutable attack history

### Quantum Engine (`/api/quantum`)
- `GET  /stats` — QBF engine stats
- `GET  /fingerprints` — Device fingerprint registry
- `POST /verify-device` — Verify device fingerprint
- `POST /register-device` — Register new fingerprint
- `GET  /attack-simulation` — Grover/Shor results
- `GET  /benchmark` — Paper Table I data

### AI Brain (`/api/ai`)
- `GET  /stats` — FL model statistics
- `GET  /imaginations` — Adversarial imaginations feed
- `GET  /model/history` — FL round history
- `POST /classify` — Classify device message
- `GET  /explain/{device_id}` — XAI explanation
- `GET  /byzantine/stats` — Byzantine defense stats

### Dashboards (`/api/dashboard`)
- `GET  /command-center` — National overview
- `GET  /traffic` — Traffic sector
- `GET  /hospital` — Hospital sector
- `GET  /water` — Water sector
- `GET  /power` — Power grid
- `GET  /compliance` — Audit dashboard

### Honeypot (`/api/honeypot`)
- `GET  /stats` — Network statistics
- `GET  /active` — Active decoys
- `GET  /intelligence` — Intelligence reports
- `GET  /intelligence/{id}` — Single report
- `POST /spawn` — Manually spawn decoys

### Simulation (`/api/simulation`)
- `GET  /status` — Simulation running state
- `POST /start` — Start virtual city
- `POST /stop` — Stop simulation
- `POST /inject-attack` — Inject test attack
- `GET  /device-types` — 8 device types
- `GET  /attack-types` — 6 attack types + detection rates

### Reports (`/api/reports`)
- `GET  /executive-summary` — 30-day overview
- `GET  /compliance` — ISO/NIST/GDPR status
- `GET  /incident-log` — Full incident history
- `GET  /threat-intelligence-summary` — Honeypot intel

### System (`/api/system`)
- `GET  /status` — All module health
- `GET  /metrics` — Performance counters
- `GET  /timeline` — Hourly attack chart
- `POST /emergency-lockdown` — Isolate sector
- `POST /restore-sector` — Restore sector

### WebSocket (`/api/ws`)
- `WS   /ws/live` — All events stream
- `WS   /ws/sector/{sector}` — Sector-specific stream

---

## Database Schema

**PostgreSQL** (structured data):
- `users` — Government personnel + roles
- `devices` — IoT device registry
- `threat_events` — Attack records
- `blockchain_records` — Chain entries
- `fl_rounds` — FL training history
- `key_records` — PQC key lifecycle
- `audit_logs` — All user actions
- `honeypot_devices` — Active decoys
- `attacker_profiles` — Captured attacker data
- `intelligence_reports` — Honeypot analysis
- `morphogenesis_events` — Topology changes

**MongoDB** (event streams):
- `events` — Raw IoT messages
- `attacks` — Attack event archive

**Redis** (cache):
- Device stats (5 min TTL)
- Threat summary (30 sec TTL)
- User sessions (30 min TTL)
- Rate limiting counters

---

## Test Results

```
64/64 tests PASS across 13 test classes:
  TestSystem       5 tests   System health endpoints
  TestAuth         8 tests   JWT + all 9 demo users
  TestRBAC         6 tests   Role-based access control
  TestDevices      4 tests   Device management
  TestThreats      3 tests   Threat intelligence
  TestBlockchain   6 tests   Blockchain + audit
  TestQuantum      4 tests   Quantum engine
  TestAIBrain      5 tests   FAC + XAI
  TestDashboards   6 tests   All sector dashboards
  TestHoneypot     4 tests   Decoy network
  TestSimulation   5 tests   Virtual city control
  TestReports      6 tests   Compliance + intelligence
  TestAlerts       2 tests   Security alerts
```
