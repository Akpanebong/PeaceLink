from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import Community, Stakeholder, TimeStampedModel


class ConflictCase(TimeStampedModel):
    class Type(models.TextChoices):
        CROP_DAMAGE = "crop_damage", "Crop damage"
        WATER_ACCESS = "water_access", "Water access"
        CATTLE_RAIDING = "cattle_raiding", "Cattle raiding"
        BOUNDARY = "boundary", "Boundary dispute"
        MARKET = "market", "Market dispute"
        OTHER = "other", "Other"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Stage(models.TextChoices):
        REPORTED = "reported", "Reported"
        ASSESSING = "assessing", "Assessing"
        MEDIATING = "mediating", "Mediating"
        AGREED = "agreed", "Agreement drafted"
        RESOLVED = "resolved", "Resolved"
        REFERRED = "referred", "Referred"

    case_id = models.CharField(max_length=32, unique=True, editable=False)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reporter_name = models.CharField(max_length=160)
    reporter_contact = models.CharField(max_length=120)
    community_a = models.ForeignKey(Community, on_delete=models.PROTECT, related_name="conflicts_as_a")
    community_b = models.ForeignKey(Community, on_delete=models.PROTECT, related_name="conflicts_as_b")
    conflict_type = models.CharField(max_length=32, choices=Type.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.MEDIUM)
    description = models.TextField()
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.REPORTED, db_index=True)
    assigned_node = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_conflicts",
        null=True,
        blank=True,
    )
    resolution_summary = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.case_id:
            count = ConflictCase.objects.count() + 1
            self.case_id = f"ADR-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.case_id} - {self.get_conflict_type_display()}"

    def get_absolute_url(self):
        return reverse("conflict_detail", kwargs={"pk": self.pk})


class CaseUpdate(TimeStampedModel):
    case = models.ForeignKey(ConflictCase, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    stage = models.CharField(max_length=20, choices=ConflictCase.Stage.choices)
    note = models.TextField()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.case.case_id} - {self.stage}"


class Referral(TimeStampedModel):
    case = models.ForeignKey(ConflictCase, on_delete=models.CASCADE, related_name="referrals")
    stakeholder = models.ForeignKey(Stakeholder, on_delete=models.PROTECT, related_name="case_referrals")
    reason = models.TextField()
    follow_up_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=(("open", "Open"), ("accepted", "Accepted"), ("closed", "Closed")),
        default="open",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.case.case_id} -> {self.stakeholder}"
