from django.apps import AppConfig


class TherapyConfig(AppConfig):
    name = "therapy"

    def ready(self):
        import therapy.api.games  # noqa
