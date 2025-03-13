# core/tests/views/test_login.py
from datetime import datetime, timezone

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


def now_timestamp():
    return int(datetime.now(timezone.utc).timestamp())


class WebLoginViewTests(TestCase):
    """Tests involving core.views.user.login_view or /login URL (browsers)"""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse("login")
        self.index_url = reverse("index")
        self.user = User.objects.create_user(  # type: ignore
            username="tester", email="test@example.com", password="password"
        )

    def test_get_returns_form(self):
        """GET request to /login returns an HTML login form."""
        resp = self.client.get(self.login_url)
        content = resp.content.decode("utf-8")
        self.assertEqual(resp.status_code, 200)
        # Check that the returned HTML contains the form elements
        self.assertIn("<form", content)
        self.assertIn('type="password"', content)
        self.assertIn('type="submit"', content)

    def test_successful_web_login_sets_session(self):
        """POST with valid credentials:
        * Should redirect to settings.LOGIN_REDIRECT_URL (HTTP 302)
        * Should set session cookie ("sessionid") indicating the user is authenticated.
        """
        data = {"username": "tester", "password": "password"}
        resp = self.client.post(self.login_url, data)
        # In Django's built-in auth, a successful login redirects.
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], settings.LOGIN_REDIRECT_URL)
        # Check that a session cookie is set
        self.assertIn("sessionid", resp.cookies)
        # Optionally, verify the session reflects the authenticated user.
        session_cookie = resp.cookies["sessionid"].value
        self.assertTrue(session_cookie, "Session cookie should not be empty")

    def test_post_login_invalid_creds_returns_error(self):
        """POST with invalid credentials should not log in.
        Standard Django auth typically redisplays the login form with an error message.
        Here we assume a response status of 200 with error message in the content.
        """
        data = {"username": "tester", "password": "wrongpassword"}
        resp = self.client.post(self.login_url, data)
        content = resp.content.decode("utf-8")
        # Depending on your customizations, Django's built-in login form re-renders with HTTP 200.
        self.assertEqual(resp.status_code, 200)
        # We assume an error indicator is present, for example an element with a class "error"
        self.assertIn("error", content.lower())

    # TODO: Let's tighten up the allowed methods later when we know more what final version will be
    # def test_non_post_get_request_returns_error(self):
    #     """If request method is neither POST or GET, return 405 Method Not Allowed"""
    #     resp_put = self.client.put(self.login_url)
    #     self.assertEqual(resp_put.status_code, 405)
    #     self.assertEqual(resp_put["Allow"], "GET, POST")
    #     self.assertIn("method", resp_put.content.decode("utf-8").lower())
    #     self.assertIn("not allowed", resp_put.content.decode("utf-8").lower())


# TODO: Adapt to login flow when doing DRF for api endpoints
# class APILoginTests(TestCase):
#     """Tests concerning core.views.api_login_view or /api/login URL"""
#
#     def setUp(self):
#         self.client = Client()
#         self.url = reverse("api_login")
#         self.user = User.objects.create(name="tester", email="test@example.com")
#         self.user.set_password("password")
#         self.user.save()
#
#     def test_valid_creds_return_valid_jwt(self):
#         """POST to /api/login w| valid creds returns:
#         200 code, plain text JWT token in body & X-Auth_token header"""
#         data = {"email": "test@example.com", "password": "password"}
#         resp = self.client.post(self.url, data)
#         token = resp.content.decode("utf-8").strip()
#         decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp["Content-Type"], "text/plain")
#         self.assertIsNotNone(token, "Token shouldn't be empty!")
#         self.assertEqual(resp["X-Auth-Token"], token)
#         self.assertEqual(decoded["name"], "tester")
#         self.assertEqual(decoded["email"], "test@example.com")
#         self.assertGreaterEqual(decoded["exp"], now_timestamp())
#
#     def test_non_post_get_request_returns_error(self):
#         """If request method is neither POST or GET, return 405 Method Not Allowed"""
#         resp_put = self.client.put(self.url)
#         self.assertEqual(resp_put.status_code, 405)
#         self.assertEqual(resp_put["Allow"], "POST")
#         self.assertIn("method", resp_put.content.decode("utf-8").lower())
#         self.assertIn("not allowed", resp_put.content.decode("utf-8").lower())
#
#     def test_post_login_invalid_creds_returns_401(self):
#         """POST with invalid creds should return 401 Unauthorized"""
#         data = {"email": "tester", "password": "wrongpassword"}
#         resp = self.client.post(self.url, data)
#         content = resp.content.decode("utf-8")
#
#         self.assertEqual(resp.status_code, 401)
#         self.assertEqual(resp["X-Error"], "true")
#         self.assertEqual(resp["Content-Type"], "text/plain")
#         self.assertIn("access", content.lower())
#         self.assertIn("unauthor", content.lower())
#         self.assertIn("invalid", content.lower())
#         self.assertIn("email", content.lower())
#         self.assertIn("password", content.lower())
#
#     def test_post_bad_email_same_as_bad_password(self):
#         """Invalid email should return same response as invalid password.
#         This obscures which field is wrong, making unauthorized logins harder."""
#         bad_mail = {"email": "bad@example.com", "password": "password"}
#         bad_pass = {"email": "test@example.com", "password": "wrongpassword"}
#         resp_bad_mail = self.client.post(self.url, bad_mail)
#         resp_bad_pass = self.client.post(self.url, bad_pass)
#         content_bad_mail = resp_bad_mail.content.decode("utf-8")
#         content_bad_pass = resp_bad_pass.content.decode("utf-8")
#
#         self.assertEqual(resp_bad_mail.status_code, resp_bad_pass.status_code)
#         self.assertEqual(resp_bad_mail["X-Error"], resp_bad_pass["X-Error"])
#         self.assertEqual(content_bad_mail, content_bad_pass)
