# core/tests/views/test_upload_api.py
from django.test import TestCase, Client
from django.urls import reverse
import logging


class UploadAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("api_upload")  # match 'name' in urls.py
        # Suppress "Method Not Allowed" logging messages during tests
        logging.getLogger("django.request").setLevel(logging.CRITICAL)

    def test_post_request_returns_200(self):
        self.assertEqual(self.client.post(self.url).status_code, 200)

    def test_get_request_returns_405(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_put_request_returns_405(self):
        self.assertEqual(self.client.put(self.url, {}).status_code, 405)

    def test_delete_request_returns_405(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)
