# ImmunoGrid — DevOps & Infrastructure

> Complete CI/CD pipeline, Docker, Kubernetes, and monitoring setup.

---

## Directory Structure

```
devops/
├── .github/
│   └── workflows/
│       └── ci.yml              GitHub Actions CI/CD (8 jobs, 346 tests)
│
├── docker/
│   ├── docker-compose.prod.yml  Production stack (nginx + all services)
│   ├── nginx.conf               Nginx reverse proxy + SSL + rate limiting
│   └── alertmanager.yml         Alert routing (email notifications)
│
├── k8s/
│   ├── deployment.yaml          API + Frontend Deployments, Ingress, HPA
│   ├── statefulsets.yaml        PostgreSQL, MongoDB, Redis StatefulSets
│   ├── services.yaml            ClusterIP services for all components
│   ├── hpa.yaml                 Horizontal Pod Autoscaler (2–20 replicas)
│   └── configmap.yaml           Non-secret config + Secret placeholder
│
└── monitoring/
    ├── prometheus.yml            Scrape config (API, DBs, system metrics)
    ├── alert_rules.yml           11 alert rules (security + infrastructure)
    └── grafana_dashboard.json    17-panel real-time dashboard
```

---

## Quick Start

### Development (Docker Compose)

```bash
# 1. Start full dev stack (API + DBs + MQTT + monitoring)
docker-compose up -d

# 2. Verify all services healthy
docker-compose ps

# Services accessible:
#   API + Docs  →  http://localhost:8000/api/docs
#   Frontend    →  http://localhost:3000
#   Prometheus  →  http://localhost:9090
#   Grafana     →  http://localhost:3001  (admin / immunogrid_admin)
```

### Production (Docker Compose)

```bash
# 1. Configure secrets
cp .env.example .env.prod
nano devops/docker/.env.prod   # fill in real passwords

# 2. Generate self-signed SSL (or use Let's Encrypt)
mkdir -p devops/docker/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout devops/docker/ssl/privkey.pem \
  -out    devops/docker/ssl/fullchain.pem \
  -subj   "/C=BD/ST=Dhaka/O=ImmunoGrid/CN=immunogrid.gov.local"

# 3. Start production stack
cd devops/docker
docker-compose -f docker-compose.prod.yml up -d

# Or via Makefile:
make docker-prod
```

### Kubernetes (AWS EKS)

```bash
# 1. Configure kubectl for your EKS cluster
aws eks update-kubeconfig --name immunogrid-cluster --region us-east-1

# 2. Create secrets (replace placeholders)
kubectl create namespace immunogrid
kubectl create secret generic immunogrid-secrets \
  --namespace immunogrid \
  --from-literal=POSTGRES_PASSWORD='your_pass' \
  --from-literal=JWT_SECRET_KEY='your_jwt_secret' \
  --from-literal=AWS_ACCESS_KEY_ID='your_key' \
  --from-literal=AWS_SECRET_ACCESS_KEY='your_secret' \
  --from-literal=BLOCKCHAIN_PRIVATE_KEY='your_blockchain_key'

# 3. Deploy all resources
kubectl apply -f devops/k8s/configmap.yaml
kubectl apply -f devops/k8s/statefulsets.yaml
kubectl apply -f devops/k8s/deployment.yaml
kubectl apply -f devops/k8s/services.yaml
kubectl apply -f devops/k8s/hpa.yaml

# 4. Verify deployment
kubectl get pods -n immunogrid
kubectl get ingress -n immunogrid

# 5. Watch rollout
kubectl rollout status deployment/immunogrid-api -n immunogrid
```

---

## CI/CD Pipeline (GitHub Actions)

### Jobs (run on every push to `main`/`develop`)

| Job | Description | Time |
|-----|-------------|------|
| `test-backend` | All 8 Python test suites (346 tests) | ~3 min |
| `test-frontend` | TypeScript check + Vite production build | ~1 min |
| `security-scan` | Bandit + Safety + secret detection | ~1 min |
| `test-go-chaincode` | Go vet + build for Fabric chaincode | ~30s |
| `build-docker` | Build API + frontend Docker images (main only) | ~3 min |
| `attack-simulation` | E2E attack simulation pipeline test | ~30s |
| `benchmark` | Research paper benchmark generation (main only) | ~2 min |
| `deployment-summary` | GitHub Step Summary with test counts | ~10s |

### Test Coverage by Job

```
test-backend:
  ✅ crypto_layer    — 32 tests  (Kyber-512, Dilithium, TLS)
  ✅ honeypot        — 22 tests  (decoy spawning, intelligence)
  ✅ iot_simulator   — 61 tests  (500 devices, 6 attackers)
  ✅ quantum_engine  — 48 tests  (QBF, Grover/Shor, BB84)
  ✅ ai_brain        — 68 tests  (FAC, GAN, XAI, FL)
  ✅ blockchain      — 33 tests  (ledger, PBFT, Web3)
  ✅ backend         — 64 tests  (64 API endpoints)
  ✅ integration     — 18 tests  (full pipeline E2E)
  ─────────────────────────────
  Total: 346 tests
```

---

## Monitoring

### Prometheus Metrics (collected from API)

| Metric | Description |
|--------|-------------|
| `immunogrid_attacks_total` | Total attacks detected (counter) |
| `immunogrid_fp_detection_rate` | Quantum FP detection rate (gauge) |
| `immunogrid_devices_online` | Online device count (gauge) |
| `immunogrid_blockchain_length` | Chain length (gauge) |
| `immunogrid_blockchain_valid` | Chain integrity (0/1 gauge) |
| `immunogrid_fl_accuracy` | FL model accuracy (gauge) |
| `immunogrid_morphogenesis_total` | Morphogenesis events (counter) |
| `immunogrid_honeypot_active` | Active honeypot count (gauge) |
| `immunogrid_honeypot_interactions_total` | Honeypot interactions (counter) |
| `immunogrid_qf_checks_total` | Quantum fingerprint checks (counter) |
| `immunogrid_impostors_detected_total` | Impostors caught (counter) |
| `immunogrid_byzantine_detected_total` | Byzantine FL clients (counter) |

### Alert Rules (11 alerts)

**Security:**
- `HighAttackRate` — >30 attacks/min (critical)
- `LowQuantumFPDetectionRate` — <90% detection (warning)
- `BlockchainIntegrityFailure` — chain invalid (critical, immediate)
- `FLModelAccuracyDrop` — <90% accuracy (warning)
- `ByzantineGradientInjection` — >3 detections/10m (critical)
- `HoneypotOverloaded` — >500 interactions (warning)

**Infrastructure:**
- `DeviceOfflineSurge` — >50 devices offline (critical)
- `APIHighErrorRate` — >5% 5xx errors (warning)
- `APIHighLatency` — p95 >2s (warning)
- `DatabaseConnectionExhausted` — >90 PG connections (critical)
- `PodCrashLooping` — >5 restarts/hr (critical)

### Grafana Dashboard

17-panel dashboard at `http://localhost:3001`:
- Detection rate, attack count, devices online, blockchain length
- Attack rate timeseries (attacks/min vs messages/min)
- Quantum FP checks per second
- FL model accuracy history
- Honeypot activity
- Threats by sector (bargauge)
- Attack type distribution (pie chart)
- API latency percentiles (p50/p95/p99)
- Pod status table (Kubernetes)
- Morphogenesis timeline

---

## Kubernetes Resources

### API Autoscaling (HPA)

```
Min replicas:  2
Max replicas:  20
Scale up on:   CPU > 70%, Memory > 80%, OR >10 attacks/min
Scale down:    5-minute stabilization (don't kill during active defense)
PDB:           minAvailable = 2 (always online)
```

### Resource Limits

| Service | CPU Request | CPU Limit | RAM Request | RAM Limit |
|---------|-------------|-----------|-------------|-----------|
| API | 500m | 2000m | 512Mi | 2Gi |
| Frontend | 100m | 500m | 128Mi | 512Mi |
| PostgreSQL | 500m | 2000m | 512Mi | 2Gi |
| MongoDB | 200m | 1000m | 256Mi | 1Gi |
| Redis | 100m | 500m | 128Mi | 768Mi |

---

## Makefile Commands

```bash
make install              # Install Python + Node deps
make test                 # Run all 346 Python tests
make test-integration     # Integration tests only
make run-backend          # FastAPI dev server
make run-frontend         # React dev server
make run-sim              # IoT city simulation
make run-orchestrator     # Full system demo
make docker-up            # Start dev Docker stack
make docker-prod          # Start production stack
make build-frontend       # Vite production build
make figures              # Generate paper figures
make benchmark            # Run research benchmarks
make clean                # Remove build artifacts
make help                 # Show all commands
```

---

## Security Notes

1. **Never commit `.env`** — use `.env.example` as template
2. **Secrets in prod** — use AWS Secrets Manager / K8s external-secrets
3. **SSL certificates** — use Let's Encrypt or AWS Certificate Manager
4. **JWT secret** — minimum 32 random characters
5. **Database passwords** — minimum 24 random characters
6. **Rate limiting** — configured in Nginx (100 req/min API, 10/min auth)
7. **MQTT TLS** — port 8883 in production, 1883 dev-only
