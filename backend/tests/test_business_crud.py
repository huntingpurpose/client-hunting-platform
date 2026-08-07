import importlib
import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class BusinessCrudTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="business-crud-", dir="/tmp")
        self.db_path = os.path.join(self.temp_dir.name, "test_businesses.sqlite")
        self.previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        import app.config as config_module
        import app.db as db_module
        import app.main as main_module
        import app.models as models_module
        import app.services.business_service as business_service_module

        self.config_module = importlib.reload(config_module)
        self.db_module = importlib.reload(db_module)
        self.models_module = importlib.reload(models_module)
        self.business_service_module = importlib.reload(business_service_module)
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

    def test_create_read_update_delete_and_list_businesses(self) -> None:
        create_payload = {
            "name": "Acme Studio",
            "category": "Design",
            "website": "https://acme.example",
            "email": "hello@acme.example",
            "phone": "+1-555-0100",
            "address": "123 Main Street",
            "city": "Seattle",
            "state": "WA",
            "country": "US",
            "postal_code": "98101",
            "latitude": 47.6062,
            "longitude": -122.3321,
            "google_maps_url": "https://maps.google.com/?q=Acme+Studio",
            "google_rating": 4.8,
            "review_count": 42,
            "business_hours": "Mon-Fri 9am-5pm",
            "facebook": "https://facebook.com/acme",
            "instagram": "https://instagram.com/acme",
            "linkedin": "https://linkedin.com/company/acme",
            "status": "active",
        }

        create_response = self.client.post("/businesses", json=create_payload)
        self.assertEqual(create_response.status_code, 201)
        created = create_response.json()
        self.assertEqual(created["name"], create_payload["name"])
        self.assertEqual(created["email"], create_payload["email"])
        self.assertEqual(created["status"], "active")
        business_id = created["id"]

        read_response = self.client.get(f"/businesses/{business_id}")
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()["id"], business_id)

        update_payload = {"city": "Portland", "state": "OR", "status": "inactive"}
        update_response = self.client.put(f"/businesses/{business_id}", json=update_payload)
        self.assertEqual(update_response.status_code, 200)
        updated = update_response.json()
        self.assertEqual(updated["city"], "Portland")
        self.assertEqual(updated["state"], "OR")
        self.assertEqual(updated["status"], "inactive")

        list_response = self.client.get("/businesses")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        delete_response = self.client.delete(f"/businesses/{business_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["deleted"], True)

        after_delete = self.client.get(f"/businesses/{business_id}")
        self.assertEqual(after_delete.status_code, 404)


if __name__ == "__main__":
    unittest.main()
