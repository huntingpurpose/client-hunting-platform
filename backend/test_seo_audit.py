import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


class SeoAuditTest(unittest.TestCase):
    @patch("app.main.requests.get")
    @patch("app.main.engine")
    def test_seo_audit_returns_h1_and_meta_and_title(self, mock_engine, mock_get):
        mock_conn = MagicMock()
        mock_row = {
            "id": 10,
            "name": "Test Business",
            "website": "https://example.com",
        }

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = mock_row
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = (
            '<html><head><title>Example Title</title>'
            '<meta name="description" content="Example description.">'
            '</head><body><h1>Heading One</h1></body></html>'
        )
        mock_get.return_value = mock_response

        client = TestClient(app)
        response = client.post("/seo-audit/10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "has_title": True,
                "title": "Example Title",
                "has_meta_description": True,
                "meta_description": "Example description.",
                "has_h1": True,
                "h1": "Heading One",
                "seo_score": 100,
            },
        )

    @patch("app.main.requests.get")
    @patch("app.main.engine")
    def test_lead_score_returns_business_id_and_scores(self, mock_engine, mock_get):
        mock_conn = MagicMock()
        mock_row = {
            "id": 10,
            "website": "https://example.com",
            "email": "hello@example.com",
            "linkedin": "https://linkedin.com/in/test",
        }

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = mock_row
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = (
            '<html><head><title>Example Title</title>'
            '<meta name="description" content="Example description.">'
            '</head><body><h1>Heading One</h1></body></html>'
        )
        mock_get.return_value = mock_response

        client = TestClient(app)
        response = client.post("/lead-score/10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "business_id": 10,
                "seo_score": 100,
                "lead_score": 100,
            },
        )

    @patch("app.main.requests.get")
    @patch("app.main.engine")
    def test_outreach_returns_template_email(self, mock_engine, mock_get):
        mock_conn = MagicMock()
        mock_row = {
            "id": 10,
            "name": "Woburn Cafe",
            "website": "https://example.com",
            "email": "hello@example.com",
            "linkedin": "https://linkedin.com/in/test",
        }

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = mock_row
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = (
            '<html><head><title>Example Title</title>'
            '<meta name="description" content="Example description.">'
            '</head><body><h1>Heading One</h1></body></html>'
        )
        mock_get.return_value = mock_response

        client = TestClient(app)
        response = client.post("/outreach/10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["subject"], "Quick idea for improving Woburn Cafe's online visibility")
        self.assertIn("Hi Woburn Cafe", data["email"])
        self.assertIn("I reviewed your online presence at https://example.com", data["email"])
        self.assertIn("SEO score is 100", data["email"])
        self.assertIn("lead score is 100", data["email"])

    @patch("app.main.requests.get")
    @patch("app.main.engine")
    def test_send_email_queues_outreach(self, mock_engine, mock_get):
        mock_conn = MagicMock()
        mock_row = {
            "id": 10,
            "name": "Woburn Cafe",
            "website": "https://example.com",
            "email": "hello@example.com",
            "linkedin": "https://linkedin.com/in/test",
        }

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = mock_row
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = (
            '<html><head><title>Example Title</title>'
            '<meta name="description" content="Example description.">'
            '</head><body><h1>Heading One</h1></body></html>'
        )
        mock_get.return_value = mock_response

        client = TestClient(app)
        response = client.post("/send-email/10", json={"to": "test@example.com"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "queued",
                "to": "test@example.com",
                "subject": "Quick idea for improving Woburn Cafe's online visibility",
                "email": response.json()["email"],
            },
        )
        self.assertIn("Hi Woburn Cafe", response.json()["email"])


if __name__ == "__main__":
    unittest.main()
