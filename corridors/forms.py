from django import forms

from .models import CorridorNotice, CorridorResponse


class CorridorNoticeForm(forms.ModelForm):
    class Meta:
        model = CorridorNotice
        fields = ("route", "herd_group", "cattle_count", "arrival_date", "message")
        widgets = {"arrival_date": forms.DateInput(attrs={"type": "date"}), "message": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class CorridorResponseForm(forms.ModelForm):
    class Meta:
        model = CorridorResponse
        fields = ("response_type", "notes")
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class CorridorNegotiationOutcomeForm(forms.ModelForm):
    class Meta:
        model = CorridorResponse
        fields = ("negotiation_outcome",)
        labels = {"negotiation_outcome": "Final negotiation response"}
        widgets = {
            "negotiation_outcome": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Record the final route decision, conditions, timing, or rejected route after negotiation.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"

    def clean_negotiation_outcome(self):
        value = self.cleaned_data["negotiation_outcome"]
        if not value:
            raise forms.ValidationError("Enter the final response from the negotiation.")
        return value
