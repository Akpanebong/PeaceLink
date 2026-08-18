from django import forms
from django.shortcuts import reverse
from core.models import Stakeholder
from .models import CaseUpdate, ConflictCase, Referral


class ConflictReportForm(forms.ModelForm):
    class Meta:
        model = ConflictCase
        fields = ("reporter_name", "reporter_contact", "community_a", "community_b", "conflict_type", "severity", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class CaseUpdateForm(forms.ModelForm):
    class Meta:
        model = CaseUpdate
        fields = ("stage", "note")
        widgets = {"note": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class ReferralForm(forms.ModelForm):
    stakeholder_type = forms.ChoiceField(
        choices=[("", "Select stakeholder type")]
        + list(Stakeholder.Type.choices),
        required=True,
        label="Stakeholder type",
    )

    class Meta:
        model = Referral
        fields = (
            "stakeholder_type",
            "stakeholder",
            "reason",
            "follow_up_date",
            "status",
        )
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 4}),
            "follow_up_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["stakeholder"].queryset = Stakeholder.objects.none()

        # If the form is being submitted, populate the stakeholder list
        # according to the selected type.
        stakeholder_type = self.data.get("referral-stakeholder_type")

        if stakeholder_type:
            self.fields["stakeholder"].queryset = (
                Stakeholder.objects
                .filter(stakeholder_type=stakeholder_type)
                .order_by("name")
            )

        self.fields["stakeholder"].widget.attrs.update({
            "class": "input",
            "data-stakeholder-url": reverse("stakeholders_by_type"),
        })

        self.fields["stakeholder_type"].widget.attrs.update({
            "class": "input",
            "id": "id_referral_stakeholder_type",
        })

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")

    def clean(self):
        cleaned_data = super().clean()

        stakeholder_type = cleaned_data.get("stakeholder_type")
        stakeholder = cleaned_data.get("stakeholder")

        if stakeholder_type and stakeholder:
            if stakeholder.stakeholder_type != stakeholder_type:
                raise forms.ValidationError(
                    "The selected stakeholder does not belong "
                    "to the selected stakeholder type."
                )

        return cleaned_data