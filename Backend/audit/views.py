from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from audit.models import AuditLog
from accounts.permissions import IsAdminUser


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = (
            "id", "actor", "actor_email", "action", "entity_type",
            "entity_id", "before_state", "after_state", "ip_address",
            "user_agent", "created_at",
        )


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = AuditLog.objects.select_related("actor").order_by("-created_at")

        entity_type = request.query_params.get("entity_type")
        action = request.query_params.get("action")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        if action:
            qs = qs.filter(action=action)

        limit = min(int(request.query_params.get("limit", 50)), 200)
        return Response(AuditLogSerializer(qs[:limit], many=True).data)
