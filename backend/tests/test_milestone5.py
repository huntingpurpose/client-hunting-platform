import importlib
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class Milestone5SeoAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="seo-", dir="/tmp")
        self.db_path = os.path.join(self.temp_dir.name, "test_seo.sqlite")
        self.previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        import app.config as config_module
        import app.db as db_module
        import app.main as main_module
        import app.models as models_module
        import app.services.seo_audit_service as seo_service_module

        self.config_module = importlib.reload(config_module)
        self.db_module = importlib.reload(db_module)
        self.models_module = importlib.reload(models_module)
        self.seo_service_module = importlib.reload(seo_service_module)
        self.main_module = importlib.reload(main_module)
        self.db_module.init_db()
        self.client = TestClient(self.main_module.app)

    def tearDown(self) -> None:
        self.client.close()
        self.temp_dir.cleanup()
        if self.previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.previous_database_url

    def test_seo_audit_endpoint_persists_and_returns_score(self) -> None:
        create_response = self.client.post(
            "/businesses",
            json={"name": "Acme Studio", "website": "https://acme.example", "phone": "+1-555-0100"},
        )
        self.assertEqual(create_response.status_code, 201)
        business_id = create_response.json()["id"]

        html = (
            "<html><head><title>Acme Studio</title>"
            "<meta name='description' content='Acme studio services.'>"
            "<meta name='keywords' content='design, branding'>"
            "<link rel='canonical' href='https://acme.example/' />"
            "<meta name='viewport' content='width=device-width, initial-scale=1' />"
            "<meta charset='utf-8' />"
            "<meta property='og:title' content='Acme Studio' />"
            "<meta property='twitter:card' content='summary' />"
            "<script src='/script.js'></script></head>"
            "<body><h1>Welcome</h1><img src='/hero.png' alt='Hero image' /></body></html>"
        )

        with patch("app.services.seo_audit_service.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.status_code = 200
            mock_response.text = html
            mock_response.url = "https://acme.example/"

            response = self.client.post(f"/seo-audit/{business_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        self.assertGreaterEqual(response.json()["score"], 0)
        self.assertIn("issues_found", response.json())

        stored = self.client.get(f"/seo-audit/{business_id}")
        self.assertEqual(stored.status_code, 200)
        self.assertEqual(stored.json()["business_id"], business_id)
        self.assertEqual(stored.json()["status"], "completed")


if __name__ == "__main__":
    unittest.main()
