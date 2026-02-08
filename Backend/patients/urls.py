from django.urls import path
from patients.views import ChildListCreateView, ChildDetailView, AdminAssignTherapistView

urlpatterns = [
    path("children", ChildListCreateView.as_view(), name="children-list-create"),
    path("children/<int:child_id>", ChildDetailView.as_view(), name="children-detail"),
    path("children/<int:child_id>/assign", AdminAssignTherapistView.as_view(), name="children-assign-therapist"),
]
