from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Community, Stakeholder
from .forms import AgreementForm
from .models import Agreement


def agreement_form_data(**overrides):
    data = {
        "community_a": overrides.pop("community_a"),
        "community_b": overrides.pop("community_b"),
        "dispute_types": ["resource_access"],
        "dispute_other": "",
        "date_signed": "2026-08-15",
        "end_date": "",
        "signing_location": "Typed location should be ignored",
        "signing_latitude": "-4.851650",
        "signing_longitude": "31.582470",
        "mediators": "Peace committee",
        "key_terms": ["shared_access"],
        "key_terms_other": "",
        "detailed_terms": "Communities agreed to shared access terms.",
        "committee_a_name": "Committee A",
        "committee_a_contact": "+211900000001",
        "committee_b_name": "Committee B",
        "committee_b_contact": "+211900000002",
        "follow_up_date": "",
        "status": Agreement.Status.ACTIVE,
        "escalation_contact": "County peace office",
    }
    data.update(overrides)
    return data


class AgreementFormTests(TestCase):
    def setUp(self):
        self.community_a = Community.objects.create(name="Bor", county="Bor")
        self.community_b = Community.objects.create(name="Twic", county="Twic")

    def test_signing_location_requires_detected_coordinates(self):
        data = agreement_form_data(
            community_a=self.community_a.pk,
            community_b=self.community_b.pk,
            signing_location="Manual location",
            signing_latitude="",
            signing_longitude="",
        )

        form = AgreementForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("Signing location must be detected automatically", form.non_field_errors()[0])

    def test_signing_location_is_derived_from_coordinates(self):
        data = agreement_form_data(community_a=self.community_a.pk, community_b=self.community_b.pk)

        form = AgreementForm(data)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["signing_location"], "Lat -4.851650, Lng 31.582470")


class AgreementViewTests(TestCase):
    def setUp(self):
        self.community_a = Community.objects.create(name="Bor", county="Bor")
        self.community_b = Community.objects.create(name="Twic", county="Twic")
        self.stakeholder = Stakeholder.objects.create(
            name="Ajak Deng",
            stakeholder_type=Stakeholder.Type.COMMUNITY_LEADER,
            designation="Paramount chief",
            email="ajak@example.com",
        )
        self.user = get_user_model().objects.create_user(username="node", password="pass", role="node")

    def test_create_page_includes_stakeholder_metadata_for_autofill(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("agreement_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"id": %s' % self.stakeholder.pk)
        self.assertContains(response, '"designation": "Paramount chief"')

    def test_detail_page_links_signing_coordinates_to_map(self):
        agreement = Agreement.objects.create(
            entered_by=self.user,
            community_a=self.community_a,
            community_b=self.community_b,
            dispute_types=["resource_access"],
            date_signed=date(2026, 8, 15),
            signing_location="Lat -4.851650, Lng 31.582470",
            signing_latitude="-4.851650",
            signing_longitude="31.582470",
            mediators="Peace committee",
            key_terms=["shared_access"],
            detailed_terms="Communities agreed to shared access terms.",
            committee_a_name="Committee A",
            committee_a_contact="+211900000001",
            committee_b_name="Committee B",
            committee_b_contact="+211900000002",
            escalation_contact="County peace office",
        )

        response = self.client.get(reverse("agreement_detail", kwargs={"pk": agreement.pk}))

        self.assertContains(response, "Open signing location on map")
        self.assertContains(response, "https://www.google.com/maps?q=-4.851650,31.582470")
