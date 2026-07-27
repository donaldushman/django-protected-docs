SECRET_KEY = "test-only-secret"
ROOT_URLCONF = "tests.urls"
ALLOWED_HOSTS = ["testserver"]
LOGIN_URL = "/accounts/login/"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "protected_docs",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates"}]
USE_TZ = True
