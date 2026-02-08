from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.conf.urls.static import static

def health(_request):
    return JsonResponse({"status": "ok"})


def ready(_request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "not_ready", "reason": "db_unreachable"}, status=503)
    return JsonResponse({"status": "ready"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health),
    path("ready", ready),

    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/patients/", include("patients.urls")),
    path("api/v1/therapy/", include("therapy.urls")),
    path("api/v1/speech/", include("speech.urls")),
    path("api/v1/compliance/", include("compliance.urls")),
    path("api/v1/audit/", include("audit.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
