import unittest
from app import app, connect, DB_PATH

class CentralV2SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        cls.client = app.test_client()

    def setUp(self):
        with self.client.session_transaction() as sess:
            sess.clear()

    def login(self):
        return self.client.post("/login?next=/", data={"username":"1","password":"1"}, follow_redirects=True)

    def test_login_page_loads(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Central", response.data)

    def test_protected_page_redirects(self):
        response = self.client.get("/produtos")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_dashboard_after_login(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PAINEL DE CONTROLE", response.data)

    def test_products_page_after_login(self):
        self.login()
        response = self.client.get("/produtos")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cat", response.data)

    def test_post_requires_csrf(self):
        self.login()
        response = self.client.post("/publicacao/nova", data={"caption":"teste"})
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
