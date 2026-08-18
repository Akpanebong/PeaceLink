from django import forms
from django.core.exceptions import ValidationError

from .models import Agreement, AgreementNotice


class AgreementForm(forms.ModelForm):
    dispute_types = forms.MultipleChoiceField(choices=Agreement.DISPUTE_TYPES, widget=forms.CheckboxSelectMultiple)
    key_terms = forms.MultipleChoiceField(choices=Agreement.KEY_TERMS, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Agreement
        fields = (
            "community_a",
            "community_b",
            "dispute_types",
            "dispute_other",
            "date_signed",
            "end_date",
            "signing_location",
            "signing_latitude",
            "signing_latitude",
            "signing_longitude",
            "mediators",
            "key_terms",
            "key_terms_other",
            "detailed_terms",
            "committee_a_name",
            "committee_a_contact",
            "committee_b_name",
            "committee_b_contact",
            "follow_up_date",
            "status",
            "escalation_contact",
        )
        widgets = {
            "date_signed": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "follow_up_date": forms.DateInput(attrs={"type": "date"}),
            "signing_latitude": forms.HiddenInput(),
            "signing_longitude": forms.HiddenInput(),
            "mediators": forms.Textarea(attrs={"rows": 3}),
            "detailed_terms": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in {"dispute_types", "key_terms"}:
                field.widget.attrs["class"] = "input"
        self.fields["signing_location"].required = False
        self.fields["signing_location"].widget.attrs.update(
            {
                "readonly": "readonly",
                "aria-readonly": "true",
                "data-location-field": "display",
                "placeholder": "Detecting signing location...",
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("signing_latitude")
        longitude = cleaned_data.get("signing_longitude")

        if latitude is None or longitude is None:
            raise ValidationError("Signing location must be detected automatically before registering the agreement.")

        cleaned_data["signing_location"] = f"Lat {latitude}, Lng {longitude}"
        return cleaned_data


class AgreementNoticeForm(forms.ModelForm):

    stakeholder_identifier = forms.CharField(
        label="Holder ID",
        required=False,
        disabled=True,
    )

    stakeholder_designation = forms.CharField(
        label="Designation",
        required=False,
        disabled=True,
    )

    class Meta:
        model = AgreementNotice

        fields = (
            "stakeholder",
            "stakeholder_identifier",
            "stakeholder_designation",
            "channel",
            "destination",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ---------------------------------------------------------
        # General styling
        # ---------------------------------------------------------
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "input"

        # ---------------------------------------------------------
        # Stakeholder select
        # ---------------------------------------------------------
        self.fields["stakeholder"].widget.attrs.update({
            "data-stakeholder-select": "true",
        })

        # ---------------------------------------------------------
        # Holder ID
        # ---------------------------------------------------------
        self.fields["stakeholder_identifier"].widget.attrs.update({
            "data-stakeholder-field": "holder_id",
            "readonly": "readonly",
            "autocomplete": "off",
        })

        # ---------------------------------------------------------
        # Designation
        # ---------------------------------------------------------
        self.fields["stakeholder_designation"].widget.attrs.update({
            "data-stakeholder-field": "designation",
            "readonly": "readonly",
            "autocomplete": "off",
        })

        # ---------------------------------------------------------
        # Channel
        # ---------------------------------------------------------
        self.fields["channel"].widget.attrs.update({
            "data-stakeholder-channel": "true",
        })

        # ---------------------------------------------------------
        # Destination
        # ---------------------------------------------------------
        self.fields["destination"].widget.attrs.update({
            "data-stakeholder-field": "destination",
            "autocomplete": "off",
        })

        # ---------------------------------------------------------
        # Existing instance
        # ---------------------------------------------------------
        if (
            self.instance
            and self.instance.pk
            and self.instance.stakeholder_id
        ):
            stakeholder = self.instance.stakeholder

            # Holder ID
            self.fields["stakeholder_identifier"].initial = (
                stakeholder.holder_id or ""
            )

            # Designation
            self.fields["stakeholder_designation"].initial = (
                stakeholder.designation or ""
            )

            # Destination
            if self.instance.channel == AgreementNotice.Channel.EMAIL:
                self.fields["destination"].initial = (
                    stakeholder.email or ""
                )

            elif self.instance.channel == AgreementNotice.Channel.SMS:
                self.fields["destination"].initial = (
                    stakeholder.phone or ""
                )

    # -------------------------------------------------------------
    # Server-side protection
    # -------------------------------------------------------------
    def clean(self):
        cleaned_data = super().clean()

        stakeholder = cleaned_data.get("stakeholder")
        channel = cleaned_data.get("channel")

        if stakeholder and channel:

            if channel == AgreementNotice.Channel.EMAIL:
                destination = stakeholder.email or ""

            elif channel == AgreementNotice.Channel.SMS:
                destination = stakeholder.phone or ""

            else:
                destination = ""

            cleaned_data["destination"] = destination

        return cleaned_data
