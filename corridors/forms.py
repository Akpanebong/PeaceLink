from django import forms

from .models import CorridorNotice, CorridorResponse, CorridorRoute


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


class CorridorRouteForm(forms.ModelForm):

    class Meta:
        model = CorridorRoute

        fields = [
            "name",
            "origin",
            "destination",
            "description",
            "risk_level",
            "active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter corridor route name"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Describe the route, important locations, "
                        "security concerns or other relevant information..."
                    ),
                    "rows": 5,
                }
            ),

            "risk_level": forms.Select(
                attrs={}
            ),
        }


    def clean(self):

        cleaned_data = super().clean()

        origin = cleaned_data.get("origin")
        destination = cleaned_data.get("destination")


        if origin and destination:

            if origin == destination:

                raise forms.ValidationError(
                    "The origin and destination communities cannot be the same."
                )


        return cleaned_data