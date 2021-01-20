from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from os.path import basename

"""
Abstract models used across the rest of the application
"""


class labeledModel(models.Model):
    label = models.CharField(
        null=False,
        blank=True,
        max_length=4000,
        default="",
        help_text="Short readable label",
    )

    class Meta:
        abstract = True

    def __str__(self):
        if self.label is None:
            return "%(class)s " + self.id
        else:
            return self.label


class URIModel(models.Model):
    uri = models.URLField(unique=True, help_text="Universal Resource Identifier")

    class Meta:
        abstract = True


class uniqueLabledModel(labeledModel):
    label = models.CharField(
        null=False,
        blank=False,
        max_length=4000,
        unique=True,
        help_text="Unique short readable label",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class descriptionModel(models.Model):
    description = models.TextField(
        null=False, blank=True, help_text="Descriptive notes"
    )

    class Meta:
        abstract = True


class sequentialModel(models.Model):
    sequence = models.PositiveIntegerField(
        db_index=True, help_text="Sequence within a set"
    )

    class Meta:
        abstract = True
        ordering = ["sequence"]


class dateCreatedModel(models.Model):
    created_on = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        db_index=True,
        help_text="Date created (automatically recorded)",
    )

    class Meta:
        abstract = True


class dateModifiedModel(dateCreatedModel):
    last_updated = models.DateTimeField(
        auto_now=True,
        editable=False,
        db_index=True,
        help_text="Date last modified (automatically recorded)",
    )

    class Meta:
        abstract = True


class userCreatedModel(models.Model):
    user_created = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        editable=False,
        null=True,
        related_name="%(class)ss_created",
        help_text="Created by user",
    )

    class Meta:
        abstract = True


class userModifiedModel(models.Model):
    user_last_modified = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        editable=False,
        null=True,
        related_name="%(class)ss_modified",
        help_text="Last modified by user",
    )

    class Meta:
        abstract = True


class trackedModel(userCreatedModel, userModifiedModel, dateModifiedModel):
    class Meta:
        abstract = True
