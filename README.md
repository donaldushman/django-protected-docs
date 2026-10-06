# django-protected-docs

Serve pre-built HTML documentation through Django while restricting it to active,
authenticated users. This is intended for low-traffic internal documentation. It
uses Django's development static-file response and is not a replacement for a
high-volume static web server.

## Installation

### Install from GitHub

Add to your `requirements.txt`:

```text
django-protected-docs @ git+https://github.com/donaldushman/django-protected-docs.git@v0.1.0
```

Or install directly:

```bash
pip install git+https://github.com/donaldushman/django-protected-docs.git@v0.1.0
```

Using a tagged release is recommended for reproducible deployments.

### Configure Django

Add the app to `INSTALLED_APPS`:

```python
# settings.py
from pathlib import Path

INSTALLED_APPS = [
    # ...
    "protected_docs",
]

# Path(BASE_DIR) supports projects where BASE_DIR is either a string or a Path.
PROTECTED_DOCS_ROOT = Path(BASE_DIR) / "docs" / "_build" / "html"
PROTECTED_DOCS_ACCESS = "superuser"
PROTECTED_DOCS_LOGIN_URL = "wagtailadmin_login"
```

`PROTECTED_DOCS_ACCESS` may be `"authenticated"`, `"staff"`, or `"superuser"`
and defaults to `"superuser"`. `PROTECTED_DOCS_LOGIN_URL` accepts anything
Django's `resolve_url()` accepts and defaults to `LOGIN_URL`.

Include the URL configuration at the desired prefix:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("docs/", include("protected_docs.urls")),
]
```

Requests to `/docs/` redirect to `/docs/index.html`. Anonymous users are sent to
the configured login view with a `next` parameter. Authenticated users without
the configured access level receive a 404 response.

## Development

Install the project with its test dependencies and run:

```console
python -m pip install -e ".[test]"
python runtests.py
```
