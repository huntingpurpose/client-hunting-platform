import importlib
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class Milestone3CollectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="collector-", dir="/tmp")
        self.db_path = os.path.join(self.temp_dir.name, "test_collector.sqlite")
        self.previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        import app.config as config_module
        import app.db as db_module
        import app.main as main_module
        import app.models as models_module
        import app.services.collector_service as collector_service_module

        self.config_module = importlib.reload(config_module)
        self.db_module = importlib.reload(db_module)
        self.models_module = importlib.reload(models_module)
        self.collector_service_module = importlib.reload(collector_service_module)
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

    def test_search_collects_and_deduplicates_businesses(self) -> None:
        sample_payload = {
            "elements": [
                {
                    "type": "node",
                    "lat": 31.5204,
                    "lon": 74.3587,
                    "tags": {
                        "name": "Lahore Dental Clinic",
                        "addr:street": "Main Boulevard",
                        "addr:city": "Lahore",
                        "addr:state": "Punjab",
                        "addr:country": "Pakistan",
                        "addr:postcode": "54000",
                        "website": "https://example.com",
                        "phone": "+92 300 1234567",
                    },
                },
                {
                    "type": "node",
                    "lat": 31.5204,
                    "lon": 74.3587,
                    "tags": {
                        "name": "Lahore Dental Clinic",
                        "addr:street": "Main Boulevard",
                        "addr:city": "Lahore",
                        "addr:state": "Punjab",
                        "addr:country": "Pakistan",
                        "addr:postcode": "54000",
                        "website": "https://example.com",
                        "phone": "+92 300 1234567",
                    },
                },
            ]
        }

        with patch("app.services.collector_service.requests.post") as mock_post:
            mock_response = mock_post.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = sample_payload

            response = self.client.post("/search", json={"query": "dentists in lahore"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["inserted"], 1)
        self.assertEqual(response.json()["duplicates"], 1)
        self.assertEqual(response.json()["total"], 2)

        stored = self.client.get("/businesses")
        self.assertEqual(stored.status_code, 200)
        self.assertEqual(len(stored.json()), 1)
        self.assertEqual(stored.json()[0]["name"], "Lahore Dental Clinic")


if __name__ == "__main__":
    unittest.main()
