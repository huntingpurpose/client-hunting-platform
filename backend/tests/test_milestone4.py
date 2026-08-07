import importlib
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class Milestone4EnrichmentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="enrichment-", dir="/tmp")
        self.db_path = os.path.join(self.temp_dir.name, "test_enrichment.sqlite")
        self.previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        import app.config as config_module
        import app.db as db_module
        import app.main as main_module
        import app.models as models_module
        import app.services.enrichment_service as enrichment_service_module

        self.config_module = importlib.reload(config_module)
        self.db_module = importlib.reload(db_module)
        self.models_module = importlib.reload(models_module)
        self.enrichment_service_module = importlib.reload(enrichment_service_module)
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

    def test_enrichment_extracts_contact_details_and_persists_them(self) -> None:
        create_response = self.client.post(
            "/businesses",
            json={"name": "Acme Studio", "website": "https://acme.example", "phone": "+1-555-0100"},
        )
        self.assertEqual(create_response.status_code, 201)
        business_id = create_response.json()["id"]

        html = (
            "<html><head><title>Acme Studio</title><meta name='author' content='Jane Doe'></head>"
            "<body><h1>Acme Studio</h1><p>Call us at +1-555-0101</p>"
            "<a href='mailto:hello@acme.example'>Email</a>"
            "<a href='https://facebook.com/acme'>Facebook</a>"
            "<a href='https://instagram.com/acme'>Instagram</a>"
            "<a href='https://linkedin.com/company/acme'>LinkedIn</a>"
            "<a href='/contact'>Contact Us</a></body></html>"
        )

        with patch("app.services.enrichment_service.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.text = html

            response = self.client.post(f"/enrich/{business_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "hello@acme.example")
        self.assertEqual(response.json()["phone"], "+1-555-0101")
        self.assertEqual(response.json()["facebook"], "https://facebook.com/acme")
        self.assertEqual(response.json()["instagram"], "https://instagram.com/acme")
        self.assertEqual(response.json()["linkedin"], "https://linkedin.com/company/acme")
        self.assertEqual(response.json()["owner_name"], "Jane Doe")

        stored = self.client.get(f"/businesses/{business_id}")
        self.assertEqual(stored.status_code, 200)
        self.assertEqual(stored.json()["email"], "hello@acme.example")
        self.assertEqual(stored.json()["phone"], "+1-555-0101")
        self.assertEqual(stored.json()["owner_name"], "Jane Doe")


if __name__ == "__main__":
    unittest.main()
