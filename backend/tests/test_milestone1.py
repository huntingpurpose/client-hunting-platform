import unittest

from fastapi.testclient import TestClient

from app.main import app


class Milestone1FoundationTest(unittest.TestCase):
    def test_health_endpoint_returns_ok(self):
        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_openapi_schema_is_available(self):
        with TestClient(app) as client:
            response = client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi", response.json())

    def test_docs_page_is_available(self):
        with TestClient(app) as client:
            response = client.get("/docs")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])


if __name__ == "__main__":
    unittest.main()
