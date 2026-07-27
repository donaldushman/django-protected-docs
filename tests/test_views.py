import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings

from protected_docs.views import serve_docs


class ProtectedDocsTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.docs_root = Path(self.temp_dir.name)
        (self.docs_root / "index.html").write_text("<h1>Internal docs</h1>")
        (self.docs_root / "style.css").write_text("body { color: navy; }")
        static_dir = self.docs_root / "_static" / "css"
        static_dir.mkdir(parents=True)
        (static_dir / "theme.css").write_text("body { color: green; }")
        self.settings_override = override_settings(
            PROTECTED_DOCS_ROOT=self.docs_root,
            PROTECTED_DOCS_ACCESS="superuser",
            PROTECTED_DOCS_LOGIN_URL="wagtailadmin_login",
        )
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.temp_dir.cleanup()

    def test_anonymous_get_redirects_to_login_with_next(self):
        response = self.client.get("/docs/index.html?print=1")
        self.assertRedirects(
            response,
            "/admin/login/?next=/docs/index.html%3Fprint%3D1",
            fetch_redirect_response=False,
        )

    def test_anonymous_head_redirects_to_login(self):
        response = self.client.head("/docs/index.html")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/login/?next=/docs/index.html")
        self.assertEqual(response.content, b"")

    def test_default_login_url_is_used_when_package_setting_is_absent(self):
        self.settings_override.disable()
        try:
            response = self.client.get("/docs/index.html")
        finally:
            self.settings_override.enable()

        self.assertRedirects(
            response,
            "/accounts/login/?next=/docs/index.html",
            fetch_redirect_response=False,
        )

    def test_superuser_can_retrieve_html_and_assets(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))
        html_response = self.client.get("/docs/index.html")
        asset_response = self.client.get("/docs/style.css")
        self.assertEqual(b"".join(html_response.streaming_content), b"<h1>Internal docs</h1>")
        self.assertEqual(b"".join(asset_response.streaming_content), b"body { color: navy; }")
        self.assertEqual(html_response["Content-Type"], "text/html")
        self.assertEqual(asset_response["Content-Type"], "text/css")

    def test_nested_sphinx_asset_can_be_retrieved(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))
        response = self.client.get("/docs/_static/css/theme.css")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b"".join(response.streaming_content),
            b"body { color: green; }",
        )

    def test_authorized_head_has_headers_and_no_body(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))
        response = self.client.head("/docs/index.html")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html")
        self.assertEqual(b"".join(response.streaming_content), b"")

    def test_authorized_responses_are_not_cacheable(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))
        response = self.client.get("/docs/index.html")

        cache_control = response["Cache-Control"]
        self.assertIn("no-store", cache_control)
        self.assertIn("private", cache_control)

    def test_ordinary_and_staff_users_receive_404_for_superuser_access(self):
        for is_staff in (False, True):
            with self.subTest(is_staff=is_staff):
                self.client.force_login(self._user(is_staff=is_staff))
                self.assertEqual(self.client.get("/docs/index.html").status_code, 404)
                self.client.logout()

    def test_inactive_user_is_not_authorized(self):
        self.client.force_login(
            self._user(is_active=False, is_staff=True, is_superuser=True)
        )
        self.assertEqual(self.client.get("/docs/index.html").status_code, 302)

    def test_staff_access(self):
        self.client.force_login(self._user(is_staff=True))
        with override_settings(PROTECTED_DOCS_ACCESS="staff"):
            self.assertEqual(self.client.get("/docs/index.html").status_code, 200)

    def test_authenticated_access(self):
        self.client.force_login(self._user())
        with override_settings(PROTECTED_DOCS_ACCESS="authenticated"):
            self.assertEqual(self.client.get("/docs/index.html").status_code, 200)

    def test_missing_file_receives_404(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))
        self.assertEqual(self.client.get("/docs/missing.html").status_code, 404)

    def test_path_traversal_is_rejected(self):
        request = RequestFactory().get("/docs/../secret.txt")
        request.user = self._user(is_staff=True, is_superuser=True)
        with self.assertRaises(Http404):
            serve_docs(request, "../secret.txt")
        with self.assertRaises(Http404):
            serve_docs(request, r"..\secret.txt")

    def test_encoded_path_traversal_is_rejected_through_url_routing(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))

        response = self.client.get("/docs/%2e%2e/secret.txt")

        self.assertEqual(response.status_code, 404)

    def test_docs_index_redirects_to_index_file(self):
        response = self.client.get("/docs/")
        self.assertRedirects(response, "/docs/index.html", fetch_redirect_response=False)

    def test_invalid_access_setting_fails_clearly(self):
        self.client.force_login(self._user())
        with override_settings(PROTECTED_DOCS_ACCESS="members"):
            with self.assertRaisesMessage(ValueError, "PROTECTED_DOCS_ACCESS"):
                self.client.get("/docs/index.html")

    def test_missing_root_fails_clearly(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))
        with override_settings(PROTECTED_DOCS_ROOT=None):
            with self.assertRaisesMessage(RuntimeError, "PROTECTED_DOCS_ROOT"):
                self.client.get("/docs/index.html")

    def test_post_is_not_allowed(self):
        self.client.force_login(self._user(is_staff=True, is_superuser=True))
        self.assertEqual(self.client.post("/docs/index.html").status_code, 405)

    def _user(self, **attributes):
        defaults = {"username": f"user-{User.objects.count()}"}
        defaults.update(attributes)
        return User.objects.create_user(**defaults)
