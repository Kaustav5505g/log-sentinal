import unittest

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


if __name__ == "__main__":
    unittest.main()
