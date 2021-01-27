from django.apps import AppConfig


class authorityConfig(AppConfig):
    name = "authority"


# def ready(self):
#     models.Authority.objects.get_or_create(label="VIAF", namespace=namespaces.VIAF)