from rest_framework import serializers


class StartSessionSerializer(serializers.Serializer):
    child_id = serializers.IntegerField()
    supervision_mode = serializers.ChoiceField(choices=["therapist", "caregiver", "mixed"], required=False, default="therapist")
    session_title = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    trials_planned = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    time_limit_ms = serializers.IntegerField(required=False, default=10000, min_value=1000, max_value=60000)


class NextTrialSerializer(serializers.Serializer):
    # purely requestless endpoint, kept for structure
    pass


class SubmitTrialSerializer(serializers.Serializer):
    clicked = serializers.CharField(required=True, allow_blank=True)  # e.g. "car" or "" on timeout
    response_time_ms = serializers.IntegerField(required=True, min_value=0, max_value=600000)
    timed_out = serializers.BooleanField(required=False, default=False)

    # Accept extra fields for scene_description game
    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        # Pass through extra fields
        for k, v in data.items():
            if k not in ret:
                ret[k] = v
        return ret


class SummarySerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    total_trials = serializers.IntegerField()
    completed_trials = serializers.IntegerField()
    correct = serializers.IntegerField()
    accuracy = serializers.FloatField()
    avg_response_time_ms = serializers.IntegerField(allow_null=True)
    current_level = serializers.IntegerField()
    suggestion = serializers.CharField(allow_blank=True)
