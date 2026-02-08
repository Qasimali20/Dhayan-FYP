from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from compliance.models import Consent
from compliance.serializers import ConsentSerializer, CreateConsentSerializer
from patients.models import ChildProfile, Guardian


class ConsentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        child_id = request.query_params.get("child_id")
        qs = Consent.objects.select_related("child", "guardian").order_by("-granted_at")
        if child_id:
            qs = qs.filter(child_id=child_id)
        return Response(ConsentSerializer(qs, many=True).data)

    def post(self, request):
        ser = CreateConsentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            child = ChildProfile.objects.get(id=ser.validated_data["child_id"])
        except ChildProfile.DoesNotExist:
            return Response({"detail": "Child not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            guardian = Guardian.objects.get(id=ser.validated_data["guardian_id"])
        except Guardian.DoesNotExist:
            return Response({"detail": "Guardian not found"}, status=status.HTTP_404_NOT_FOUND)

        consent = Consent.objects.create(
            child=child,
            guardian=guardian,
            consent_type=ser.validated_data["consent_type"],
            scope=ser.validated_data.get("scope", {}),
            created_by=request.user,
        )

        return Response(ConsentSerializer(consent).data, status=status.HTTP_201_CREATED)


class ConsentRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, consent_id: int):
        try:
            consent = Consent.objects.get(id=consent_id)
        except Consent.DoesNotExist:
            return Response({"detail": "Consent not found"}, status=status.HTTP_404_NOT_FOUND)

        if consent.revoked_at:
            return Response({"detail": "Already revoked"}, status=status.HTTP_400_BAD_REQUEST)

        consent.revoked_at = timezone.now()
        consent.save()
        return Response(ConsentSerializer(consent).data)
