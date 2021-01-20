from django.apps import AppConfig


class entityConfig(AppConfig):
    name = "entity"

    def ready(self):
        import entity.signals