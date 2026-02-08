from django.urls import path
from compliance.views import ConsentListCreateView, ConsentRevokeView

urlpatterns = [
    path("consents", ConsentListCreateView.as_view(), name="consent-list-create"),
    path("consents/<int:consent_id>/revoke", ConsentRevokeView.as_view(), name="consent-revoke"),
]
