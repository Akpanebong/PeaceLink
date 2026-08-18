from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.translations import language_choices
from phonenumber_field.modelfields import PhoneNumberField


class Profile(AbstractUser):
    class Role(models.TextChoices):
        MEMBER = "member", _("Community member")
        NODE = "node", _("Community node")
        COORDINATOR = "coordinator", _("Coordinator")
        PARTNER = "partner", _("Partner observer")

    class PreferredLanguage(models.TextChoices):
        ENGLISH = "en", _("English")
        JUBA_ARABIC = "juba_arabic", _("Juba Arabic")
        KISWAHILI = "sw", _("Kiswahili")
        ARABIC = "ar", _("Arabic")
        DINKA = "din", _("Dinka")
        NUER = "nus", _("Nuer")
        BARI = "bfa", _("Bari")
        ZANDE = "zne", _("Zande")
        SHILLUK = "shk", _("Shilluk")

    role = models.CharField(max_length=24, choices=Role.choices, default=Role.MEMBER, db_index=True)
    # Store complete international phone numbers using django-phonenumber-field
    phone = PhoneNumberField(max_length=32, unique=True, blank=True, null=True)
    community = models.ForeignKey(
        "core.Community",
        on_delete=models.SET_NULL,
        related_name="members",
        null=True,
        blank=True,
    )
    organization = models.CharField(max_length=160, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    preferred_language = models.CharField(
        max_length=24,
        choices=language_choices,
        default=PreferredLanguage.ENGLISH,
    )
    trust_score = models.PositiveSmallIntegerField(default=60)
    ussd_identifier = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ("first_name", "last_name", "username")

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_community_node(self):
        return self.role in {self.Role.NODE, self.Role.COORDINATOR} or self.is_superuser

    @property
    def can_manage_intelligence(self):
        return self.role == self.Role.COORDINATOR or self.is_staff or self.is_superuser
