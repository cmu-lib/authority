from django.db import models
from authority import mixins
from entity.models import Person


class Authority(mixins.trackedModel, mixins.uniqueLabledModel, mixins.descriptionModel):
    namespace = models.URLField(unique=True)

    class Meta:
        abstract = False
        verbose_name_plural = "authorities"


class CloseMatch(mixins.trackedModel):
    entity = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="close_matches"
    )
    authority = models.ForeignKey(
        Authority, on_delete=models.CASCADE, related_name="close_matches"
    )
    identifier = models.CharField(max_length=1000)

    class Meta:
        unique_together = (("entity", "authority"), ("authority", "identifier"))
        verbose_name_plural = "close matches"