from decimal import Decimal, InvalidOperation

from django import forms

from .models import TradeConnection, TradeOffer


class TradeOfferForm(forms.ModelForm):
    class Meta:
        model = TradeOffer
        fields = ("commodity", "category", "quantity", "offer_type", "community", "location", "contact_method", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class TradeConnectionForm(forms.ModelForm):
    class Meta:
        model = TradeConnection
        fields = ("message",)
        widgets = {"message": forms.Textarea(attrs={"rows": 3, "placeholder": "Share your contact preference or proposed exchange."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs["class"] = "input"


class TradeConnectionAcceptForm(forms.ModelForm):
    class Meta:
        model = TradeConnection
        fields = ("quantity_sold",)
        labels = {"quantity_sold": "Quantity sold"}

    def __init__(self, *args, **kwargs):
        self.offer = kwargs.pop("offer")
        self.connection = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        self.fields["quantity_sold"].widget.attrs.update({"class": "input", "min": "0.01", "step": "0.01"})

    def clean_quantity_sold(self):
        quantity = self.cleaned_data["quantity_sold"]
        if quantity <= 0:
            raise forms.ValidationError("Enter a quantity greater than zero.")

        remaining = self.offer.remaining_quantity
        if remaining is None:
            return quantity

        current_quantity = self.connection.quantity_sold if self.connection and self.connection.accepted else Decimal("0")
        try:
            available = Decimal(str(remaining)) + current_quantity
        except InvalidOperation:
            return quantity

        if available <= 0:
            raise forms.ValidationError("All available quantity has already been sold.")
        if quantity > available:
            raise forms.ValidationError(f"Only {available} is available for this trade.")
        return quantity
