from datetime import datetime
import hashlib
import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Community(TimeStampedModel):
    name = models.CharField(max_length=160)
    ethnic_group = models.CharField(max_length=80, blank=True)
    county = models.CharField(max_length=120)
    payam = models.CharField(max_length=120, blank=True)
    boma = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    trust_score = models.PositiveSmallIntegerField(default=60)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("county", "name")
        verbose_name_plural = "communities"

    def __str__(self):
        return f"{self.name} - {self.county}"


class Stakeholder(TimeStampedModel):
    class Type(models.TextChoices):
        GOVERNMENT = "government", "Government"
        NGO = "ngo", "Non-government org."
        COMMUNITY_LEADER = "community_leader", "Local community leader"
        RELIGIOUS_LEADER = "religious_leader", "Religious leader"
        OTHER = "other", "Other"

    stakeholder_type = models.CharField(max_length=32, choices=Type.choices)
    name = models.CharField(max_length=160)
    designation = models.CharField(max_length=160, blank=True)
    organization = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    communities = models.ManyToManyField(Community, related_name="stakeholders", blank=True)
    active = models.BooleanField(default=True)
    holder_id = models.CharField(blank=True, null=False, editable=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # First save to generate the primary key
        super().save(*args, **kwargs)

        # Generate holder_id after pk exists
        if is_new and not self.holder_id:
            year_short = str(datetime.now().year)[-2:]
            self.holder_id = f"PL-{year_short}-{self.pk:03d}"

            # Save only the generated holder_id
            super().save(update_fields=["holder_id"])


    class Meta:
        ordering = ("stakeholder_type", "name")

    def __str__(self):
        return self.name


class Alert(TimeStampedModel):
    class Level(models.TextChoices):
        INFO = "info", "Info"
        WATCH = "watch", "Watch"
        ALERT = "alert", "Alert"
        ACTION = "action", "Action"

    title = models.CharField(max_length=160)
    message = models.TextField()
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.INFO)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="alerts", null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="alerts", null=True, blank=True,)
    action_url = models.CharField(max_length=240, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.action_url or reverse("home")


class Activity(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    verb = models.CharField(max_length=120)
    detail = models.CharField(max_length=240)
    accent = models.CharField(max_length=20, default="teal")
    happened_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-happened_at", "-created_at")
        verbose_name_plural = "activities"

    def __str__(self):
        return f"{self.verb}: {self.detail}"


class TranslationCache(TimeStampedModel):
    source_language = models.CharField(max_length=24, default="en")
    target_language = models.CharField(max_length=24, db_index=True)
    source_hash = models.CharField(max_length=64, db_index=True)
    source_text = models.TextField()
    translated_text = models.TextField()
    provider = models.CharField(max_length=40, default="openai")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_hash", "target_language"),
                name="unique_translation_source_target",
            )
        ]
        ordering = ("target_language", "source_hash")

    def __str__(self):
        return f"{self.source_language}->{self.target_language}: {self.source_text[:60]}"

    @staticmethod
    def hash_text(text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
