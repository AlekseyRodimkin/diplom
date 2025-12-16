from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("warehouse:main"), name="root_redirect"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("account/", include("allauth.urls")),
    path("warehouse/", include("warehouse.urls")),
    path("warehouse/", include("structure.urls")),
    path("warehouse/", include("staff.urls")),
    path("warehouse/", include("wave.urls")),
    path("terminal/", include("terminal.urls")),
]

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
