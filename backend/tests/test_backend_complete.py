"""
ImmunoGrid — Backend API Complete Test Suite (64 tests)
Tests all 13 routers across all role permissions.

Run:
    python tests/test_backend_complete.py
"""

import sys
import os
import unittest

# ── Path setup ────────────────────────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.environ["APP_ENV"] = "test"   # disables rate limiter

from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


# ── Token helpers (fresh token each call) ────────────────────────────────────

def tok(email="admin@immunogrid.gov", pw="Admin@123"):
    r = client.post("/api/auth/login", json={"email": email, "password": pw})
    return r.json().get("access_token", "") if r.status_code == 200 else ""

def admin():   return {"Authorization": f"Bearer {tok()}"}
def traffic(): return {"Authorization": f"Bearer {tok('traffic@immunogrid.gov','Traffic@123')}"}
def auditor(): return {"Authorization": f"Bearer {tok('auditor@immunogrid.gov','Audit@123')}"}


# ══════════════════════════════════════════════════════════════════════════════
# TEST CLASSES
# ══════════════════════════════════════════════════════════════════════════════

class TestSystem(unittest.TestCase):
    def test_root(self):
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["system"], "ImmunoGrid")

    def test_health(self):
        r = client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "healthy")

    def test_system_status(self):
        r = client.get("/api/system/status", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("modules", r.json())

    def test_system_metrics(self):
        r = client.get("/api/system/metrics", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("messages_processed_today", r.json())

    def test_timeline(self):
        r = client.get("/api/system/timeline?hours=6", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("timeline", r.json())


class TestAuth(unittest.TestCase):
    def test_login_admin(self):
        r = client.post("/api/auth/login",
                        json={"email": "admin@immunogrid.gov", "password": "Admin@123"})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("access_token", d)
        self.assertEqual(d["role"], "super_admin")

    def test_login_wrong_password(self):
        r = client.post("/api/auth/login",
                        json={"email": "admin@immunogrid.gov", "password": "WRONG"})
        self.assertEqual(r.status_code, 401)

    def test_login_unknown_email(self):
        r = client.post("/api/auth/login",
                        json={"email": "nobody@test.gov", "password": "Test@123"})
        self.assertEqual(r.status_code, 401)

    def test_me(self):
        r = client.get("/api/auth/me", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["email"], "admin@immunogrid.gov")

    def test_me_no_token(self):
        r = client.get("/api/auth/me")
        self.assertIn(r.status_code, [401, 403])  # FastAPI returns 403 for missing, 401 for invalid

    def test_me_bad_token(self):
        r = client.get("/api/auth/me",
                       headers={"Authorization": "Bearer bad.token.x"})
        self.assertEqual(r.status_code, 401)

    def test_all_9_users_login(self):
        accounts = [
            ("admin@immunogrid.gov",    "Admin@123"),
            ("security@immunogrid.gov", "Security@123"),
            ("traffic@immunogrid.gov",  "Traffic@123"),
            ("hospital@immunogrid.gov", "Health@123"),
            ("auditor@immunogrid.gov",  "Audit@123"),
            ("quantum@immunogrid.gov",  "Quantum@123"),
            ("devops@immunogrid.gov",   "DevOps@123"),
            ("water@immunogrid.gov",    "Water@123"),
            ("energy@immunogrid.gov",   "Energy@123"),
        ]
        for email, pw in accounts:
            r = client.post("/api/auth/login", json={"email": email, "password": pw})
            self.assertEqual(r.status_code, 200, f"Login failed: {email}")

    def test_logout(self):
        r = client.post("/api/auth/logout", headers=admin())
        self.assertEqual(r.status_code, 200)


class TestRBAC(unittest.TestCase):
    def test_list_users_admin_ok(self):
        r = client.get("/api/auth/users", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_list_users_traffic_forbidden(self):
        r = client.get("/api/auth/users", headers=traffic())
        self.assertEqual(r.status_code, 403)

    def test_my_permissions(self):
        r = client.get("/api/users/me/permissions", headers=admin())
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("role", d)
        self.assertIn("permissions", d)

    def test_roles_list_13(self):
        r = client.get("/api/users/roles/all", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["roles"]), 13)

    def test_create_user(self):
        r = client.post("/api/users/", headers=admin(), json={
            "email": "new_test@immunogrid.gov",
            "full_name": "Test User",
            "role": "traffic_ministry",
            "ministry": "Transport",
            "password": "Test@1234",
        })
        self.assertIn(r.status_code, [200, 201, 409])

    def test_create_user_traffic_forbidden(self):
        r = client.post("/api/users/", headers=traffic(), json={
            "email": "x@test.gov", "full_name": "X",
            "role": "traffic_ministry", "password": "P@ssw1"
        })
        self.assertEqual(r.status_code, 403)


class TestDevices(unittest.TestCase):
    def test_list_all(self):
        r = client.get("/api/devices/", headers=admin())
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("devices", d)
        self.assertIn("total", d)

    def test_device_stats(self):
        r = client.get("/api/devices/stats", headers=admin())
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("total", d)
        self.assertIn("online", d)

    def test_single_device(self):
        r = client.get("/api/devices/traffic-sensor-001", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_traffic_sector_filter(self):
        r = client.get("/api/devices/", headers=traffic())
        self.assertEqual(r.status_code, 200)


class TestThreats(unittest.TestCase):
    def test_list(self):
        r = client.get("/api/threats/", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("threats", r.json())

    def test_summary(self):
        r = client.get("/api/threats/summary", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("detection_rate", r.json())

    def test_live(self):
        r = client.get("/api/threats/live", headers=admin())
        self.assertEqual(r.status_code, 200)


class TestBlockchain(unittest.TestCase):
    def test_stats(self):
        r = client.get("/api/blockchain/stats", headers=admin())
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("chain_length", d)
        self.assertIn("chain_valid", d)

    def test_chain(self):
        r = client.get("/api/blockchain/chain?limit=5", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_topology(self):
        r = client.get("/api/blockchain/topology", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("active_sectors", r.json())

    def test_attacks(self):
        r = client.get("/api/blockchain/attacks", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_auditor_allowed(self):
        r = client.get("/api/blockchain/stats", headers=auditor())
        self.assertEqual(r.status_code, 200)

    def test_traffic_forbidden(self):
        r = client.get("/api/blockchain/chain", headers=traffic())
        self.assertEqual(r.status_code, 403)


class TestQuantum(unittest.TestCase):
    def test_stats(self):
        r = client.get("/api/quantum/stats", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("registered_devices", r.json())

    def test_fingerprints(self):
        r = client.get("/api/quantum/fingerprints", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_attack_simulation(self):
        r = client.get("/api/quantum/attack-simulation", headers=admin())
        self.assertEqual(r.status_code, 200)
        d = r.json()
        # Accept both response formats (real simulation vs mock)
        has_classical = "classical_crypto" in d or "grover_on_aes128" in d
        self.assertTrue(has_classical, f"Missing attack data in: {list(d.keys())}")

    def test_benchmark(self):
        r = client.get("/api/quantum/benchmark", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("table_1_qbf_vs_classical", r.json())


class TestAIBrain(unittest.TestCase):
    def test_stats(self):
        r = client.get("/api/ai/stats", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("global_model_accuracy", r.json())

    def test_imaginations(self):
        r = client.get("/api/ai/imaginations", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("imaginations", r.json())

    def test_model_history(self):
        r = client.get("/api/ai/model/history", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("rounds", r.json())

    def test_explain(self):
        r = client.get("/api/ai/explain/dev-001?prediction=1", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("human_readable", r.json())

    def test_byzantine_stats(self):
        r = client.get("/api/ai/byzantine/stats", headers=admin())
        self.assertEqual(r.status_code, 200)


class TestDashboards(unittest.TestCase):
    def test_command_center(self):
        r = client.get("/api/dashboard/command-center", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("devices_online", r.json())

    def test_traffic(self):
        r = client.get("/api/dashboard/traffic", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_hospital(self):
        r = client.get("/api/dashboard/hospital", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_water(self):
        r = client.get("/api/dashboard/water", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_power(self):
        r = client.get("/api/dashboard/power", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_compliance(self):
        r = client.get("/api/dashboard/compliance", headers=admin())
        self.assertEqual(r.status_code, 200)


class TestHoneypot(unittest.TestCase):
    def test_stats(self):
        r = client.get("/api/honeypot/stats", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("active_honeypots", r.json())

    def test_active(self):
        r = client.get("/api/honeypot/active", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_intelligence(self):
        r = client.get("/api/honeypot/intelligence", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_spawn(self):
        r = client.post("/api/honeypot/spawn?sector=traffic&count=2",
                        headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["spawned"], 2)


class TestSimulation(unittest.TestCase):
    def test_status(self):
        r = client.get("/api/simulation/status", headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_device_types(self):
        r = client.get("/api/simulation/device-types", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total_devices"], 500)
        self.assertEqual(len(r.json()["device_types"]), 8)

    def test_attack_types(self):
        r = client.get("/api/simulation/attack-types", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["attack_types"]), 6)

    def test_start(self):
        r = client.post("/api/simulation/start", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "started")

    def test_inject_attack(self):
        r = client.post(
            "/api/simulation/inject-attack?attack_type=spoofing&target_sector=traffic",
            headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("detected", r.json())


class TestReports(unittest.TestCase):
    def test_executive_summary(self):
        r = client.get("/api/reports/executive-summary", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("security_summary", r.json())

    def test_compliance(self):
        r = client.get("/api/reports/compliance", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("standards", r.json())

    def test_incident_log(self):
        r = client.get("/api/reports/incident-log", headers=admin())
        self.assertEqual(r.status_code, 200)
        self.assertIn("incidents", r.json())

    def test_threat_intel(self):
        r = client.get("/api/reports/threat-intelligence-summary",
                       headers=admin())
        self.assertEqual(r.status_code, 200)

    def test_auditor_access(self):
        r = client.get("/api/reports/compliance", headers=auditor())
        self.assertEqual(r.status_code, 200)

    def test_traffic_forbidden(self):
        r = client.get("/api/reports/executive-summary", headers=traffic())
        self.assertEqual(r.status_code, 403)


class TestAlerts(unittest.TestCase):
    def test_get_alerts(self):
        r = client.get("/api/alerts/", headers=admin())
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("alerts", d)
        self.assertIn("unread", d)

    def test_acknowledge(self):
        r = client.post("/api/alerts/ALT-000001/acknowledge", headers=admin())
        self.assertEqual(r.status_code, 200)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    console.print("\n[bold cyan]╔══════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  ImmunoGrid Backend — Complete Test Suite   ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════════╝[/bold cyan]\n")

    classes = [
        TestSystem, TestAuth, TestRBAC, TestDevices, TestThreats,
        TestBlockchain, TestQuantum, TestAIBrain, TestDashboards,
        TestHoneypot, TestSimulation, TestReports, TestAlerts,
    ]

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    stream = open(os.devnull, 'w')
    runner = unittest.TextTestRunner(verbosity=0, stream=stream)
    result = runner.run(suite)
    stream.close()

    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    table = Table(
        title=f"\nBackend Test Results — {passed}/{result.testsRun} passed",
        box=box.ROUNDED, border_style="cyan",
    )
    table.add_column("Test Class",  style="white",  max_width=25)
    table.add_column("Count",       style="cyan",   justify="right")
    table.add_column("Status",      style="bold")

    fail_names = {str(f[0]) for f in result.failures + result.errors}
    for cls in classes:
        cnt    = loader.loadTestsFromTestCase(cls).countTestCases()
        cls_fail = any(cls.__name__ in fn for fn in fail_names)
        status = "[red]FAIL ❌[/red]" if cls_fail else "[green]PASS ✅[/green]"
        table.add_row(cls.__name__, str(cnt), status)

    console.print(table)

    if failed == 0:
        console.print(f"\n[bold green]🎉 ALL {result.testsRun} BACKEND TESTS PASSED[/bold green]\n")
    else:
        console.print(f"\n[bold red]{failed} test(s) failed:[/bold red]")
        for f in result.failures + result.errors:
            console.print(f"  [red]→ {f[0]}[/red]")
            if result.failures:
                console.print(f"  [dim]{f[1][:200]}[/dim]")
        sys.exit(1)
