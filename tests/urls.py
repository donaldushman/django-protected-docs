from django.http import HttpResponse
from django.urls import include, path


def wagtail_login(request):
    return HttpResponse("login")


urlpatterns = [
    path("admin/login/", wagtail_login, name="wagtailadmin_login"),
    path("docs/", include("protected_docs.urls")),
]

