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


if __name__ == "__main__":
    unittest.main()
