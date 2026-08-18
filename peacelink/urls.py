from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("account/", include("account.urls")),
    path("trade/", include("trade.urls")),
    path("corridors/", include("corridors.urls")),
    path("agreements/", include("agreements.urls")),
    path("conflicts/", include("conflicts.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
