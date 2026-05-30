from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.views.i18n import set_language

from courses.views import LandingPageView

urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", LandingPageView.as_view(), name="landing"),
    path("accounts/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("payments/", include("payments.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("panel/", include("dashboard.panel_urls")),
    path("api/", include("api.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
