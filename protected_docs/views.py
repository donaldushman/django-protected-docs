from pathlib import PurePosixPath

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import resolve_url
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe
from django.views.static import serve


VALID_ACCESS_LEVELS = {"authenticated", "staff", "superuser"}


def _user_can_view_docs(user):
    access = getattr(settings, "PROTECTED_DOCS_ACCESS", "superuser")
    if access not in VALID_ACCESS_LEVELS:
        choices = ", ".join(sorted(VALID_ACCESS_LEVELS))
        raise ValueError(f"PROTECTED_DOCS_ACCESS must be one of: {choices}")

    if not user.is_authenticated or not user.is_active:
        return False
    if access == "authenticated":
        return True
    if access == "staff":
        return user.is_staff
    return user.is_superuser


def _validate_path(path):
    """Reject paths which could escape the configured documentation root."""
    parsed = PurePosixPath(path.replace("\\", "/"))
    if parsed.is_absolute() or ".." in parsed.parts:
        raise Http404


@never_cache
@require_safe
def serve_docs(request, path="index.html"):
    if not request.user.is_authenticated:
        login_url = resolve_url(
            getattr(settings, "PROTECTED_DOCS_LOGIN_URL", settings.LOGIN_URL)
        )
        return redirect_to_login(request.get_full_path(), login_url)

    if not _user_can_view_docs(request.user):
        # Do not advertise the existence of internal documentation.
        raise Http404

    document_root = getattr(settings, "PROTECTED_DOCS_ROOT", None)
    if not document_root:
        raise RuntimeError("PROTECTED_DOCS_ROOT is not configured")

    _validate_path(path)
    return serve(
        request,
        path,
        document_root=document_root,
        show_indexes=False,
    )
