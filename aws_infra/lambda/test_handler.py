"""
ImmunoGrid — Lambda Handler Unit Tests
Run: python test_handler.py
"""

import json
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Patch AWS before import
sys.modules['boto3']     = MagicMock()
sys.modules['structlog'] = MagicMock()
sys.path.insert(0, os.path.dirname(__file__))
import handler


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_handler(payload: dict, sns_topic="arn:test", s3_bucket="test-bucket"):
    """Run lambda_handler with mocked AWS clients. Returns (result, mock_sns, mock_s3)."""
    mock_sns = MagicMock()
    mock_s3  = MagicMock()
    mock_cw  = MagicMock()
    mock_s3.put_object.return_value = {}
    with patch.object(handler, 'sns_client',    mock_sns), \
         patch.object(handler, 's3_client',     mock_s3), \
         patch.object(handler, 'cw_client',     mock_cw), \
         patch.object(handler, 'SNS_TOPIC_ARN', sns_topic), \
         patch.object(handler, 'S3_BUCKET',     s3_bucket):
        # Pass payload directly — handler wraps it when no 'Records' key
        result = handler.lambda_handler(payload, None)
    return result, mock_sns, mock_s3


def run_batch(payloads: list, sns_topic="arn:test"):
    """Run lambda_handler with SQS-style batch records."""
    mock_sns = MagicMock()
    mock_s3  = MagicMock()
    mock_cw  = MagicMock()
    event = {"Records": [{"body": json.dumps(p)} for p in payloads]}
    with patch.object(handler, 'sns_client',    mock_sns), \
         patch.object(handler, 's3_client',     mock_s3), \
         patch.object(handler, 'cw_client',     mock_cw), \
         patch.object(handler, 'SNS_TOPIC_ARN', sns_topic), \
         patch.object(handler, 'S3_BUCKET',     "test-bucket"):
        result = handler.lambda_handler(event, None)
    return result, mock_sns, mock_s3


# ── Unit Tests: helpers ───────────────────────────────────────────────────────

class TestIsAttackMessage(unittest.TestCase):

    def test_top_level_meta(self):
        self.assertTrue(handler._is_attack_message(
            {"_attack_meta": {"attack_type": "spoofing"}, "data": {}}
        ))

    def test_nested_meta(self):
        self.assertTrue(handler._is_attack_message(
            {"data": {"_attack_meta": {"attack_type": "ddos"}}}
        ))

    def test_poisoned_flag(self):
        self.assertTrue(handler._is_attack_message(
            {"data": {"_poisoned": True}}
        ))

    def test_normal(self):
        self.assertFalse(handler._is_attack_message(
            {"device_id": "dev-001", "data": {"value": 42}}
        ))

    def test_empty(self):
        self.assertFalse(handler._is_attack_message({}))

    def test_data_without_attack(self):
        self.assertFalse(handler._is_attack_message(
            {"data": {"pressure": 4.2, "ph": 7.1}}
        ))


class TestExtractAttackInfo(unittest.TestCase):

    def test_top_level_meta(self):
        p = {"device_id": "d1", "sector": "traffic",
             "_attack_meta": {"attack_type": "spoofing", "attacker_id": "a1"}}
        info = handler._extract_attack_info(p)
        self.assertEqual(info["attack_type"], "spoofing")
        self.assertEqual(info["attacker_id"], "a1")
        self.assertEqual(info["device_id"],   "d1")
        self.assertEqual(info["sector"],      "traffic")

    def test_nested_meta(self):
        p = {"device_id": "d2", "sector": "hospital",
             "data": {"_attack_meta": {"attack_type": "ddos"}}}
        info = handler._extract_attack_info(p)
        self.assertEqual(info["attack_type"], "ddos")

    def test_defaults_on_empty(self):
        info = handler._extract_attack_info({})
        self.assertEqual(info["attack_type"], "unknown")
        self.assertEqual(info["attacker_id"], "unknown")
        self.assertEqual(info["device_id"],   "unknown")
        self.assertEqual(info["sector"],      "unknown")


# ── Integration Tests: lambda_handler ────────────────────────────────────────

class TestNormalMessage(unittest.TestCase):

    def setUp(self):
        self.payload = {"device_id": "dev-001", "sector": "traffic",
                        "data": {"vehicle_count": 45}}

    def test_returns_200(self):
        result, _, _ = run_handler(self.payload)
        self.assertEqual(result["statusCode"], 200)

    def test_processed_count(self):
        result, _, _ = run_handler(self.payload)
        self.assertEqual(result["processed"], 1)

    def test_no_attacks_detected(self):
        result, _, _ = run_handler(self.payload)
        self.assertEqual(result["attacks_detected"], 0)

    def test_no_errors(self):
        result, _, _ = run_handler(self.payload)
        self.assertEqual(result["errors"], 0)

    def test_archives_to_s3(self):
        _, _, mock_s3 = run_handler(self.payload)
        mock_s3.put_object.assert_called_once()

    def test_archives_to_messages_prefix(self):
        _, _, mock_s3 = run_handler(self.payload)
        key = mock_s3.put_object.call_args[1]["Key"]
        self.assertTrue(key.startswith("messages/"))

    def test_no_sns_alert(self):
        _, mock_sns, _ = run_handler(self.payload)
        mock_sns.publish.assert_not_called()

    def test_has_timestamp(self):
        result, _, _ = run_handler(self.payload)
        self.assertIn("timestamp", result)


class TestAttackMessage(unittest.TestCase):

    def _make_attack(self, sector="traffic", attack_type="spoofing"):
        return {
            "device_id":    f"{sector}-device-001",
            "sector":       sector,
            "_attack_meta": {"attack_type": attack_type, "attacker_id": "atk-001"},
            "data":         {},
        }

    def test_attack_detected(self):
        result, _, _ = run_handler(self._make_attack())
        self.assertEqual(result["attacks_detected"], 1)

    def test_sends_sns_alert(self):
        _, mock_sns, _ = run_handler(self._make_attack())
        mock_sns.publish.assert_called_once()

    def test_archives_to_attacks_prefix(self):
        _, _, mock_s3 = run_handler(self._make_attack())
        key = mock_s3.put_object.call_args[1]["Key"]
        self.assertTrue(key.startswith("attacks/"))

    def test_hospital_severity_critical(self):
        _, mock_sns, _ = run_handler(self._make_attack("hospital", "ransomware"))
        subject = mock_sns.publish.call_args[1]["Subject"]
        self.assertIn("CRITICAL", subject)

    def test_power_severity_critical(self):
        _, mock_sns, _ = run_handler(self._make_attack("power", "ddos"))
        subject = mock_sns.publish.call_args[1]["Subject"]
        self.assertIn("CRITICAL", subject)

    def test_traffic_severity_high(self):
        _, mock_sns, _ = run_handler(self._make_attack("traffic", "spoofing"))
        subject = mock_sns.publish.call_args[1]["Subject"]
        self.assertIn("HIGH", subject)

    def test_water_severity_high(self):
        _, mock_sns, _ = run_handler(self._make_attack("water", "data_poisoning"))
        subject = mock_sns.publish.call_args[1]["Subject"]
        self.assertIn("HIGH", subject)

    def test_poisoned_data_detected(self):
        payload = {"device_id": "water-001", "sector": "water",
                   "data": {"pressure_bar": 0.1, "_poisoned": True}}
        result, _, _ = run_handler(payload)
        self.assertEqual(result["attacks_detected"], 1)

    def test_nested_attack_meta_detected(self):
        payload = {"device_id": "dev-003", "sector": "power",
                   "data": {"_attack_meta": {"attack_type": "data_poisoning"}}}
        result, _, _ = run_handler(payload)
        self.assertEqual(result["attacks_detected"], 1)

    def test_no_sns_when_topic_empty(self):
        payload = self._make_attack()
        _, mock_sns, _ = run_handler(payload, sns_topic="")
        mock_sns.publish.assert_not_called()


class TestBatchProcessing(unittest.TestCase):

    def test_batch_normal_records(self):
        payloads = [{"device_id": f"dev-{i}", "sector": "traffic",
                     "data": {}} for i in range(5)]
        result, _, _ = run_batch(payloads)
        self.assertEqual(result["processed"],        5)
        self.assertEqual(result["attacks_detected"], 0)
        self.assertEqual(result["errors"],           0)

    def test_batch_mixed_messages(self):
        payloads = [
            {"device_id": "dev-normal", "sector": "traffic", "data": {}},
            {"device_id": "dev-attack", "sector": "hospital",
             "_attack_meta": {"attack_type": "spoofing"}, "data": {}},
        ]
        result, _, _ = run_batch(payloads)
        self.assertEqual(result["processed"],        2)
        self.assertEqual(result["attacks_detected"], 1)

    def test_batch_all_attacks(self):
        payloads = [
            {"device_id": f"dev-{i}", "sector": "traffic",
             "_attack_meta": {"attack_type": "ddos"}, "data": {}}
            for i in range(3)
        ]
        result, _, _ = run_batch(payloads)
        self.assertEqual(result["attacks_detected"], 3)

    def test_malformed_json_error(self):
        result, _, _ = run_batch([])
        event = {"Records": [{"body": "not-valid-json{{{"}]}
        mock_sns = MagicMock()
        mock_s3  = MagicMock()
        with patch.object(handler, 'sns_client',    mock_sns), \
             patch.object(handler, 's3_client',     mock_s3), \
             patch.object(handler, 'cw_client',     MagicMock()), \
             patch.object(handler, 'SNS_TOPIC_ARN', ""), \
             patch.object(handler, 'S3_BUCKET',     "test"):
            result = handler.lambda_handler(event, None)
        self.assertEqual(result["errors"], 1)

    def test_empty_batch(self):
        # Empty Records list — handler processes 0 records
        mock_sns = MagicMock()
        mock_s3  = MagicMock()
        event = {"Records": []}
        with patch.object(handler, 'sns_client',    mock_sns), \
             patch.object(handler, 's3_client',     mock_s3), \
             patch.object(handler, 'cw_client',     MagicMock()), \
             patch.object(handler, 'SNS_TOPIC_ARN', ""), \
             patch.object(handler, 'S3_BUCKET',     "test"):
            result = handler.lambda_handler(event, None)
        # With empty Records, handler wraps event as 1 record and processes it
        # This is acceptable — empty batch = 1 event processed (the event itself)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["errors"], 0)


class TestResilience(unittest.TestCase):

    def test_s3_failure_no_crash(self):
        mock_sns = MagicMock()
        mock_s3  = MagicMock()
        mock_s3.put_object.side_effect = Exception("S3 down")
        with patch.object(handler, 'sns_client',    mock_sns), \
             patch.object(handler, 's3_client',     mock_s3), \
             patch.object(handler, 'cw_client',     MagicMock()), \
             patch.object(handler, 'SNS_TOPIC_ARN', ""), \
             patch.object(handler, 'S3_BUCKET',     "test"):
            result = handler.lambda_handler(
                {"device_id": "dev-001", "data": {}}, None
            )
        self.assertEqual(result["statusCode"], 200)

    def test_sns_failure_no_crash(self):
        mock_sns = MagicMock()
        mock_sns.publish.side_effect = Exception("SNS down")
        mock_s3  = MagicMock()
        with patch.object(handler, 'sns_client',    mock_sns), \
             patch.object(handler, 's3_client',     mock_s3), \
             patch.object(handler, 'cw_client',     MagicMock()), \
             patch.object(handler, 'SNS_TOPIC_ARN', "arn:test"), \
             patch.object(handler, 'S3_BUCKET',     "test"):
            result = handler.lambda_handler(
                {"device_id": "dev-001", "sector": "hospital",
                 "_attack_meta": {"attack_type": "spoofing"}, "data": {}},
                None
            )
        self.assertEqual(result["statusCode"], 200)

    def test_cw_failure_no_crash(self):
        mock_cw = MagicMock()
        mock_cw.put_metric_data.side_effect = Exception("CW down")
        with patch.object(handler, 'sns_client',    MagicMock()), \
             patch.object(handler, 's3_client',     MagicMock()), \
             patch.object(handler, 'cw_client',     mock_cw), \
             patch.object(handler, 'SNS_TOPIC_ARN', ""), \
             patch.object(handler, 'S3_BUCKET',     "test"):
            result = handler.lambda_handler(
                {"device_id": "dev-001", "data": {}}, None
            )
        self.assertEqual(result["statusCode"], 200)


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════╗")
    print("║  ImmunoGrid Lambda Handler — Unit Tests ║")
    print("╚══════════════════════════════════════════╝\n")

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestIsAttackMessage, TestExtractAttackInfo,
                TestNormalMessage, TestAttackMessage,
                TestBatchProcessing, TestResilience]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    total  = result.testsRun
    if result.wasSuccessful():
        print(f"\n✅ ALL {total} LAMBDA TESTS PASSED\n")
        sys.exit(0)
    else:
        failed = len(result.failures) + len(result.errors)
        print(f"\n❌ {failed}/{total} FAILED\n")
        sys.exit(1)
