from django.shortcuts import redirect
from django.urls import re_path
from django.views.decorators.http import require_safe

from .views import serve_docs

app_name = "protected_docs"


@require_safe
def docs_index(request):
    return redirect("protected_docs:file", path="index.html")


urlpatterns = [
    re_path(r"^$", docs_index, name="index"),
    re_path(r"^(?P<path>.+)$", serve_docs, name="file"),
]

