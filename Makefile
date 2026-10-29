# ImmunoGrid — Build, Test & Deploy Makefile
# Usage: make <target>   |   make help

.PHONY: all install test test-all test-crypto test-honeypot test-iot test-quantum \
        test-ai test-blockchain test-backend test-integration run-sim run-backend   \
        run-frontend run-orchestrator build-frontend build-contracts docker-up      \
        docker-down docker-prod docker-logs docker-ps figures benchmark             \
        deploy-contracts-local deploy-contracts-testnet verify-contracts            \
        seed-contracts terraform-init terraform-plan terraform-apply                \
        k8s-deploy k8s-status k8s-logs k8s-delete ci-local lint-py lint-ts         \
        clean clean-docker clean-k8s help

# ── Colors ────────────────────────────────────────────────────────────────────
CYAN  := \033[0;36m
GREEN := \033[0;32m
YELLOW:= \033[1;33m
RED   := \033[0;31m
RESET := \033[0m

# ── Configuration ─────────────────────────────────────────────────────────────
PYTHON    := python
PIP       := pip
NPM       := npm
DOCKER    := docker
KUBECTL   := kubectl
TERRAFORM := terraform
K8S_NS    := immunogrid

# ════════════════════════════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════════════════════════════

install:
	@echo "$(CYAN)Installing Python dependencies...$(RESET)"
	$(PIP) install -r requirements.txt
	@echo "$(CYAN)Installing frontend dependencies...$(RESET)"
	cd frontend && $(NPM) ci
	@echo "$(GREEN)✅ All dependencies installed$(RESET)"

install-dev:
	$(PIP) install -r requirements.txt bandit safety detect-secrets
	cd frontend && $(NPM) ci
	@echo "$(GREEN)✅ Dev dependencies installed$(RESET)"

# ════════════════════════════════════════════════════════════════════════════════
# TESTS
# ════════════════════════════════════════════════════════════════════════════════

test-all: test-crypto test-honeypot test-iot test-quantum test-ai test-blockchain test-backend test-integration
	@echo ""
	@echo "$(GREEN)🎉 ALL TEST SUITES PASSED$(RESET)"
	@echo "   346 tests across 8 modules"

test: test-all

test-crypto:
	@echo "$(CYAN)Testing Crypto Layer (32 tests)...$(RESET)"
	$(PYTHON) crypto_layer/test_crypto_complete.py

test-honeypot:
	@echo "$(CYAN)Testing Honeypot (22 tests)...$(RESET)"
	$(PYTHON) honeypot/test_honeypot_complete.py

test-iot:
	@echo "$(CYAN)Testing IoT Simulator (61 tests)...$(RESET)"
	$(PYTHON) iot_simulator/test_iot_simulator_complete.py

test-quantum:
	@echo "$(CYAN)Testing Quantum Engine (48 tests)...$(RESET)"
	$(PYTHON) quantum_engine/test_quantum_engine_complete.py

test-ai:
	@echo "$(CYAN)Testing AI Brain (68 tests)...$(RESET)"
	$(PYTHON) ai_brain/test_ai_brain_complete.py

test-blockchain:
	@echo "$(CYAN)Testing Blockchain (33 tests)...$(RESET)"
	$(PYTHON) blockchain/test_blockchain_complete.py

test-backend:
	@echo "$(CYAN)Testing Backend API (64 tests)...$(RESET)"
	$(PYTHON) backend/tests/test_backend_complete.py

test-integration:
	@echo "$(CYAN)Running Integration Tests (18 tests)...$(RESET)"
	$(PYTHON) test_integration.py

test-solidity:
	@echo "$(CYAN)Running Solidity contract tests...$(RESET)"
	cd blockchain/solidity && npx hardhat test

test-go:
	@echo "$(CYAN)Checking Go chaincode...$(RESET)"
	cd blockchain/chaincode && go vet ./... && go build ./...
	@echo "$(GREEN)✅ Go chaincode: OK$(RESET)"

# ════════════════════════════════════════════════════════════════════════════════
# CODE QUALITY
# ════════════════════════════════════════════════════════════════════════════════

lint-py:
	@echo "$(CYAN)Running Bandit security scan...$(RESET)"
	bandit -r iot_simulator quantum_engine blockchain ai_brain crypto_layer honeypot \
	       backend -ll --exclude "*/test_*,*/__pycache__/*" || true
	@echo "$(CYAN)Checking dependencies for vulnerabilities...$(RESET)"
	safety check -r requirements.txt --continue-on-error || true

lint-ts:
	@echo "$(CYAN)TypeScript type check...$(RESET)"
	cd frontend && npx tsc --noEmit
	@echo "$(GREEN)✅ TypeScript: OK$(RESET)"

lint: lint-py lint-ts

# ════════════════════════════════════════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════════════════════════════════════════

run-backend:
	@echo "$(CYAN)Starting Backend API (port 8000)...$(RESET)"
	cd backend && uvicorn main:app --reload --port 8000

run-frontend:
	@echo "$(CYAN)Starting Frontend dev server (port 3000)...$(RESET)"
	cd frontend && $(NPM) run dev

run-sim:
	@echo "$(CYAN)Starting IoT City Simulation (500+ devices)...$(RESET)"
	$(PYTHON) start.py sim

run-quantum:
	$(PYTHON) start.py quantum

run-attack:
	$(PYTHON) start.py attack

run-orchestrator:
	@echo "$(CYAN)Starting full system orchestrator...$(RESET)"
	$(PYTHON) system_orchestrator.py

run-all:
	@echo "$(YELLOW)Start backend and frontend in separate terminals:$(RESET)"
	@echo "  Terminal 1: make run-backend"
	@echo "  Terminal 2: make run-frontend"
	@echo "  Terminal 3: make run-sim"

# ════════════════════════════════════════════════════════════════════════════════
# BUILD
# ════════════════════════════════════════════════════════════════════════════════

build-frontend:
	@echo "$(CYAN)Building frontend for production...$(RESET)"
	cd frontend && $(NPM) run build
	@echo "$(GREEN)✅ Frontend built: frontend/dist/$(RESET)"

build-contracts:
	@echo "$(CYAN)Compiling Solidity contracts...$(RESET)"
	cd blockchain/solidity && npx hardhat compile

build-images:
	@echo "$(CYAN)Building Docker images...$(RESET)"
	$(DOCKER) build -t immunogrid/api:latest ./backend
	$(DOCKER) build -t immunogrid/frontend:latest -f frontend/Dockerfile.frontend ./frontend
	@echo "$(GREEN)✅ Docker images built$(RESET)"

# ════════════════════════════════════════════════════════════════════════════════
# DOCKER
# ════════════════════════════════════════════════════════════════════════════════

docker-up:
	@echo "$(CYAN)Starting Docker dev stack...$(RESET)"
	$(DOCKER) compose up -d
	@echo ""
	@echo "$(GREEN)✅ Services started:$(RESET)"
	@echo "   API + Docs  → http://localhost:8000/api/docs"
	@echo "   Frontend    → http://localhost:3000"
	@echo "   Prometheus  → http://localhost:9090"
	@echo "   Grafana     → http://localhost:3001  (admin / immunogrid_admin)"
	@echo "   Postgres    → localhost:5432"
	@echo "   MongoDB     → localhost:27017"
	@echo "   Redis       → localhost:6379"
	@echo "   MQTT        → localhost:1883"

docker-down:
	@echo "$(CYAN)Stopping Docker stack...$(RESET)"
	$(DOCKER) compose down

docker-down-v:
	@echo "$(RED)Stopping Docker stack + removing volumes...$(RESET)"
	$(DOCKER) compose down -v

docker-prod:
	@echo "$(CYAN)Starting PRODUCTION Docker stack...$(RESET)"
	cd devops/docker && $(DOCKER) compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Production stack started$(RESET)"

docker-prod-down:
	cd devops/docker && $(DOCKER) compose -f docker-compose.prod.yml down

docker-logs:
	$(DOCKER) compose logs -f api

docker-ps:
	$(DOCKER) compose ps

docker-restart:
	$(DOCKER) compose restart api

docker-rebuild:
	$(DOCKER) compose up -d --build api

# ════════════════════════════════════════════════════════════════════════════════
# RESEARCH PAPER
# ════════════════════════════════════════════════════════════════════════════════

figures:
	@echo "$(CYAN)Generating paper figures...$(RESET)"
	$(PIP) install matplotlib seaborn -q
	cd paper && $(PYTHON) generate_figures.py
	@echo "$(GREEN)✅ Figures saved to paper/figures/$(RESET)"

benchmark:
	@echo "$(CYAN)Running crypto benchmark (Table II)...$(RESET)"
	cd crypto_layer && $(PYTHON) benchmark.py
	@echo ""
	@echo "$(CYAN)Running quantum benchmark (Tables I, III, IV)...$(RESET)"
	cd quantum_engine && $(PYTHON) -c "\
	import sys; sys.path.insert(0, '..')\n\
	from benchmark import ImmunoGridBenchmark\n\
	b = ImmunoGridBenchmark()\n\
	r = b.run_all()\n\
	print(f'QBF accuracy:      {r[\"table_1_fingerprint\"][\"quantum_fingerprinting\"][\"accuracy\"]}%')\n\
	print(f'PQC overhead:      {r[\"table_2_crypto\"][\"total_pqc_ms\"]}ms')\n\
	print(f'Detection rate:    {r[\"table_3_detection\"][\"overall_rate\"]}%')\n\
	print(f'FL convergence:    round {r[\"table_4_fl\"][\"convergence_round\"]}')\n\
	"
	@echo "$(GREEN)✅ Benchmarks complete. See quantum_engine/benchmark_results.json$(RESET)"

# ════════════════════════════════════════════════════════════════════════════════
# BLOCKCHAIN / SOLIDITY
# ════════════════════════════════════════════════════════════════════════════════

deploy-contracts-local:
	@echo "$(CYAN)Deploying Solidity contracts to local Hardhat node...$(RESET)"
	cd blockchain/solidity && npx hardhat node &
	sleep 3
	cd blockchain/solidity && npx hardhat run scripts/deploy.js --network hardhat
	cd blockchain/solidity && npx hardhat run scripts/seed_data.js --network hardhat

deploy-contracts-testnet:
	@echo "$(CYAN)Deploying to Sepolia testnet...$(RESET)"
	cd blockchain/solidity && npx hardhat run scripts/deploy.js --network sepolia

verify-contracts:
	cd blockchain/solidity && npx hardhat run scripts/verify.js --network hardhat

seed-contracts:
	cd blockchain/solidity && npx hardhat run scripts/seed_data.js --network hardhat

interact-contracts:
	cd blockchain/solidity && npx hardhat run scripts/interact.js --network hardhat

# ════════════════════════════════════════════════════════════════════════════════
# AWS TERRAFORM
# ════════════════════════════════════════════════════════════════════════════════

terraform-init:
	@echo "$(CYAN)Initializing Terraform...$(RESET)"
	cd aws_infra/terraform && $(TERRAFORM) init

terraform-plan:
	cd aws_infra/terraform && $(TERRAFORM) plan -var="environment=dev"

terraform-apply:
	@echo "$(YELLOW)Applying Terraform (dev)...$(RESET)"
	cd aws_infra/terraform && $(TERRAFORM) apply -var="environment=dev" -auto-approve

terraform-destroy:
	@echo "$(RED)Destroying Terraform resources...$(RESET)"
	cd aws_infra/terraform && $(TERRAFORM) destroy -auto-approve

# ════════════════════════════════════════════════════════════════════════════════
# KUBERNETES
# ════════════════════════════════════════════════════════════════════════════════

k8s-deploy:
	@echo "$(CYAN)Deploying to Kubernetes...$(RESET)"
	$(KUBECTL) apply -f devops/k8s/configmap.yaml
	$(KUBECTL) apply -f devops/k8s/statefulsets.yaml
	$(KUBECTL) apply -f devops/k8s/deployment.yaml
	$(KUBECTL) apply -f devops/k8s/services.yaml
	$(KUBECTL) apply -f devops/k8s/hpa.yaml
	@echo "$(GREEN)✅ Kubernetes deployment applied$(RESET)"
	$(KUBECTL) get pods -n $(K8S_NS)

k8s-status:
	$(KUBECTL) get all -n $(K8S_NS)

k8s-logs:
	$(KUBECTL) logs -n $(K8S_NS) -l app=immunogrid-api --tail=100 -f

k8s-events:
	$(KUBECTL) get events -n $(K8S_NS) --sort-by='.lastTimestamp'

k8s-rollout:
	$(KUBECTL) rollout status deployment/immunogrid-api -n $(K8S_NS)

k8s-delete:
	@echo "$(RED)Deleting Kubernetes resources...$(RESET)"
	$(KUBECTL) delete namespace $(K8S_NS) --ignore-not-found

k8s-port-forward:
	$(KUBECTL) port-forward -n $(K8S_NS) svc/immunogrid-api-svc 8000:8000

# ════════════════════════════════════════════════════════════════════════════════
# CI (run locally to simulate GitHub Actions)
# ════════════════════════════════════════════════════════════════════════════════

ci-local: lint test-all build-frontend
	@echo ""
	@echo "$(GREEN)✅ Full CI pipeline passed locally$(RESET)"

# ════════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════════════════════════

clean:
	@echo "$(CYAN)Cleaning Python artifacts...$(RESET)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pkl" -delete 2>/dev/null || true
	find . -name "benchmark_results.json" -delete 2>/dev/null || true
	find . -name "immunogrid_training_dataset.csv" -delete 2>/dev/null || true
	@echo "$(CYAN)Cleaning frontend build...$(RESET)"
	cd frontend && rm -rf dist 2>/dev/null || true
	@echo "$(CYAN)Cleaning Solidity artifacts...$(RESET)"
	cd blockchain/solidity && rm -rf artifacts cache 2>/dev/null || true
	@echo "$(GREEN)✅ Cleaned$(RESET)"

clean-docker:
	@echo "$(RED)Removing all ImmunoGrid Docker containers + images...$(RESET)"
	$(DOCKER) compose down -v --remove-orphans 2>/dev/null || true
	$(DOCKER) rmi immunogrid/api:latest immunogrid/frontend:latest 2>/dev/null || true

clean-k8s:
	$(KUBECTL) delete namespace $(K8S_NS) --ignore-not-found

# ════════════════════════════════════════════════════════════════════════════════
# HELP
# ════════════════════════════════════════════════════════════════════════════════

help:
	@echo ""
	@echo "$(CYAN)ImmunoGrid — Available Make Targets$(RESET)"
	@echo "$(CYAN)=====================================$(RESET)"
	@echo ""
	@echo "$(YELLOW)Setup$(RESET)"
	@echo "  install                Install Python + Node.js dependencies"
	@echo "  install-dev            Install + dev/security tools"
	@echo ""
	@echo "$(YELLOW)Tests$(RESET)"
	@echo "  test                   Run ALL 346 tests across 8 modules"
	@echo "  test-crypto            Crypto Layer    (32 tests)"
	@echo "  test-honeypot          Honeypot        (22 tests)"
	@echo "  test-iot               IoT Simulator   (61 tests)"
	@echo "  test-quantum           Quantum Engine  (48 tests)"
	@echo "  test-ai                AI Brain        (68 tests)"
	@echo "  test-blockchain        Blockchain      (33 tests)"
	@echo "  test-backend           Backend API     (64 tests)"
	@echo "  test-integration       Integration     (18 tests)"
	@echo "  test-solidity          Solidity contracts"
	@echo "  test-go                Go chaincode syntax check"
	@echo ""
	@echo "$(YELLOW)Code Quality$(RESET)"
	@echo "  lint                   Run Bandit + TypeScript checks"
	@echo "  lint-py                Bandit + Safety (Python)"
	@echo "  lint-ts                TypeScript type check"
	@echo ""
	@echo "$(YELLOW)Run$(RESET)"
	@echo "  run-backend            FastAPI dev server   (:8000)"
	@echo "  run-frontend           React dev server     (:3000)"
	@echo "  run-sim                IoT City Simulation  (500 devices)"
	@echo "  run-orchestrator       Full system demo (all 7 modules)"
	@echo ""
	@echo "$(YELLOW)Build$(RESET)"
	@echo "  build-frontend         Vite production build"
	@echo "  build-contracts        Compile Solidity contracts"
	@echo "  build-images           Build Docker images"
	@echo ""
	@echo "$(YELLOW)Docker$(RESET)"
	@echo "  docker-up              Start dev stack (all services)"
	@echo "  docker-down            Stop dev stack"
	@echo "  docker-prod            Start production stack"
	@echo "  docker-logs            Follow API container logs"
	@echo "  docker-ps              List running containers"
	@echo ""
	@echo "$(YELLOW)Research Paper$(RESET)"
	@echo "  figures                Generate paper figures"
	@echo "  benchmark              Run Tables I–IV benchmarks"
	@echo ""
	@echo "$(YELLOW)Blockchain / Solidity$(RESET)"
	@echo "  deploy-contracts-local Deploy to local Hardhat node"
	@echo "  deploy-contracts-testnet Deploy to Sepolia testnet"
	@echo "  verify-contracts       Post-deploy verification"
	@echo "  seed-contracts         Seed demo data"
	@echo ""
	@echo "$(YELLOW)AWS / Kubernetes$(RESET)"
	@echo "  terraform-init         Initialize Terraform"
	@echo "  terraform-plan         Preview changes"
	@echo "  terraform-apply        Deploy to AWS"
	@echo "  k8s-deploy             Apply all K8s manifests"
	@echo "  k8s-status             Show pod/service status"
	@echo "  k8s-logs               Stream API pod logs"
	@echo ""
	@echo "$(YELLOW)CI$(RESET)"
	@echo "  ci-local               Run full CI pipeline locally"
	@echo ""
	@echo "$(YELLOW)Cleanup$(RESET)"
	@echo "  clean                  Remove build artifacts"
	@echo "  clean-docker           Remove containers + images"
	@echo ""
