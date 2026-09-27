import unittest
import os
import sqlite3
from app import app, init_db, check_url, DB_NAME

class UptimeBuddyTests(unittest.TestCase):

    def setUp(self):
        # Use a fresh test database before each test
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    def test_dashboard_loads(self):
        """Homepage should load successfully"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_add_valid_url(self):
        """Adding a URL should store it and show it on the dashboard"""
        response = self.client.post("/add", data={"url": "https://example.com"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"example.com", response.data)

    def test_add_empty_url_does_not_crash(self):
        """Submitting an empty URL should not crash the app"""
        response = self.client.post("/add", data={"url": ""}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_check_url_function_up(self):
        """check_url() should correctly identify a working site as UP"""
        status, code, resp_time = check_url("https://www.google.com")
        self.assertEqual(status, "UP")
        self.assertEqual(code, 200)

    def test_check_url_function_down(self):
        """check_url() should correctly identify an invalid URL as DOWN"""
        status, code, resp_time = check_url("https://this-domain-does-not-exist-xyz123.com")
        self.assertEqual(status, "DOWN")

if __name__ == "__main__":
    unittest.main()