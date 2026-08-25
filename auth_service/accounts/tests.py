from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class AuthServiceTests(APITestCase):
    def signup(self, username="malek", password="test12345"):
        return self.client.post(
            "/api/auth/signup/",
            {"username": username, "email": "m@example.com", "password": password},
            format="json",
        )

    def login(self, username="malek", password="test12345"):
        return self.client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )

    def test_signup_creates_user(self):
        response = self.signup()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="malek").exists())
        self.assertNotIn("password", response.data)

    def test_signup_short_password_rejected(self):
        response = self.signup(password="123")
        self.assertEqual(response.status_code, 400)

    def test_login_returns_tokens(self):
        self.signup()
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password_rejected(self):
        self.signup()
        response = self.login(password="wrongpass")
        self.assertEqual(response.status_code, 401)

    def test_me_blocked_without_token(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_works_with_token(self):
        self.signup()
        token = self.login().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "malek")
