from django.conf import settings
from django.db import models
from django.urls import reverse
from urllib.parse import quote_plus

from core.models import Community, Stakeholder, TimeStampedModel


class Agreement(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        UNDER_REVIEW = "under_review", "Under Review"
        BREACHED = "breached", "Breached"
        FULFILLED = "fulfilled", "Fulfilled"

    DISPUTE_TYPES = (
        ("cattle_raiding", "Cattle raiding"),
        ("land_boundary", "Land-boundary"),
        ("resource_access", "Resource-access"),
        ("other", "Other"),
    )
    KEY_TERMS = (
        ("cessation", "Cessation of hostilities"),
        ("return_property", "Return of captured property / livestock"),
        ("compensation", "Compensation arrangement"),
        ("boundary", "Boundary / land-use clarification"),
        ("shared_access", "Shared access arrangement"),
        ("early_warning", "Early-warning reporting and future non-violence"),
        ("other", "Other"),
    )

    agreement_id = models.CharField(max_length=32, unique=True, editable=False)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="agreements_entered")
    community_a = models.ForeignKey(Community, on_delete=models.PROTECT, related_name="agreements_as_a")
    community_b = models.ForeignKey(Community, on_delete=models.PROTECT, related_name="agreements_as_b")
    dispute_types = models.JSONField(default=list)
    dispute_other = models.CharField(max_length=160, blank=True)
    date_signed = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    signing_location = models.CharField(max_length=200)
    signing_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    signing_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    mediators = models.TextField(help_text="Names and affiliation")
    key_terms = models.JSONField(default=list)
    key_terms_other = models.CharField(max_length=200, blank=True)
    detailed_terms = models.TextField()
    committee_a_name = models.CharField(max_length=160)
    committee_a_contact = models.CharField(max_length=120)
    committee_b_name = models.CharField(max_length=160)
    committee_b_contact = models.CharField(max_length=120)
    follow_up_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE)
    escalation_contact = models.CharField(max_length=200)
    stakeholders = models.ManyToManyField(Stakeholder, through="AgreementNotice", related_name="agreements")

    class Meta:
        ordering = ("-date_signed", "-created_at")

    def save(self, *args, **kwargs):
        if not self.agreement_id:
            year = self.date_signed.year if self.date_signed else "NEW"
            count = Agreement.objects.count() + 1
            self.agreement_id = f"PL-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.agreement_id}: {self.community_a} / {self.community_b}"

    def get_absolute_url(self):
        return reverse("agreement_detail", kwargs={"pk": self.pk})

    @property
    def signing_map_url(self):
        if self.signing_latitude is not None and self.signing_longitude is not None:
            return f"https://www.google.com/maps?q={self.signing_latitude},{self.signing_longitude}"
        if self.signing_location:
            return f"https://www.google.com/maps/search/?api=1&query={quote_plus(self.signing_location)}"
        return ""


class AgreementNotice(TimeStampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "Phone / SMS"

    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name="notices")
    stakeholder = models.ForeignKey(Stakeholder, on_delete=models.PROTECT, related_name="agreement_notices")
    channel = models.CharField(max_length=12, choices=Channel.choices, default=Channel.EMAIL)
    destination = models.CharField(max_length=160)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=80, default="queued")

    class Meta:
        ordering = ("stakeholder__stakeholder_type", "stakeholder__name")

    def __str__(self):
        return f"{self.agreement.agreement_id} -> {self.stakeholder}"
