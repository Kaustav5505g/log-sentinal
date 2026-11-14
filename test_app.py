import unittest
from unittest.mock import patch

from app import app


class HealthCheckTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "healthy", "service": "LogSentinel"},
        )

    def test_prediction_logs_server_timestamp(self):
        with patch("app.classify_log", return_value=1):
            with self.assertLogs(app.logger, level="INFO") as log:
                response = self.client.post(
                    "/predict",
                    json={
                        "request_count": 150,
                        "error_rate": 0.03,
                        "response_time": 120.0,
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            log.output[0],
            r"Telemetry evaluated at \d{4}-\d{2}-\d{2}T"
            r"\d{2}:\d{2}:\d{2}\.\d{6}",
        )

    def test_prediction_rejects_empty_json(self):
        response = self.client.post("/predict", json={})
        self.assertIn(response.status_code, [400, 422])

    def test_prediction_rejects_missing_fields(self):
        response = self.client.post("/predict", json={"request_count": 150})
        self.assertIn(response.status_code, [400, 422])

    def test_prediction_rejects_invalid_data_types(self):
        response = self.client.post(
            "/predict",
            json={
                "request_count": "not-a-number",
                "error_rate": 0.03,
                "response_time": 120.0,
                "cpu_usage": 55.0,
                "memory_usage": 50.0,
                "active_connections": 95,
                "network_in": 17.0,
                "network_out": 14.0,
            },
        )
        self.assertIn(response.status_code, [400, 422])

    def test_prediction_rejects_non_json_payload(self):
        response = self.client.post(
            "/predict",
            data="plain text payload",
            content_type="text/plain",
        )
        self.assertIn(response.status_code, [400, 415, 422])


if __name__ == "__main__":
    unittest.main()
