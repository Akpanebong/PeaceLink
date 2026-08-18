import phonenumbers

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import SplitPhoneNumberField

from .models import Profile
from .utils import get_country_choices


class CountryPhoneNumberField(SplitPhoneNumberField):
    default_error_messages = {
        **SplitPhoneNumberField.default_error_messages,
        "country_mismatch": "Enter a phone number that belongs to the selected country.",
    }

    def prefix_field(self):
        field = forms.ChoiceField(choices=get_country_choices())
        field.widget.attrs.update(
            {
                "class": "phone-country-select",
                "aria-label": "Country calling code",
            }
        )
        return field

    def clean(self, value):
        clean_value = super().clean(value)

        if clean_value in self.empty_values or not value:
            return clean_value

        selected_region = value[0] if len(value) > 0 else None
        parsed_region = phonenumbers.region_code_for_number(clean_value)

        if selected_region and parsed_region and parsed_region != selected_region:
            raise ValidationError(
                self.error_messages["country_mismatch"],
                code="country_mismatch",
            )

        return clean_value

    def number_field(self):
        field = super().number_field()
        field.widget.attrs.update(
            {
                "class": "phone-number-input",
                "placeholder": "Phone number",
                "aria-label": "Phone number",
            }
        )
        return field


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, "widgets"):
                continue

            css_class = "checkbox" if isinstance(field.widget, forms.CheckboxInput) else "input"
            existing_class = field.widget.attrs.get("class")
            field.widget.attrs["class"] = (
                f"{existing_class} {css_class}" if existing_class else css_class
            )


class RegistrationForm(StyledFormMixin, UserCreationForm):
    phone = CountryPhoneNumberField(
        required=False,
        label="Phone number",
        help_text="Select your country and enter the local phone number.",
    )

    class Meta:
        model = Profile
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "community",
            "role",
            "preferred_language",
            "organization",
            "designation",
            "ussd_identifier",
        )


class ProfileForm(StyledFormMixin, forms.ModelForm):
    phone = CountryPhoneNumberField(
        required=False,
        label="Phone number",
        help_text="Select your country and enter the local phone number.",
    )

    class Meta:
        model = Profile
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "community",
            "role",
            "preferred_language",
            "organization",
            "designation",
            "ussd_identifier",
        )
