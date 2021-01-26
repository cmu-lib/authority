from django.db import models
from authority import mixins


class Authority(mixins.trackedModel, mixins.uniqueLabledModel, mixins.descriptionModel):
    namespace = models.URLField(unique=True)

    class Meta:
        abstract = False
        verbose_name_plural = "authorities"


class CloseMatch(mixins.trackedModel):
    entity = models.ForeignKey(
        "entity.Person", on_delete=models.CASCADE, related_name="close_matches"
    )
    authority = models.ForeignKey(
        Authority, on_delete=models.CASCADE, related_name="close_matches"
    )
    identifier = models.URLField(help_text="URI for this entity in this authority.")

    class Meta:
        unique_together = (("entity", "authority"), ("authority", "identifier"))
        verbose_name_plural = "close matches"