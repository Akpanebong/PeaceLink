from django import forms

from .models import Community, Stakeholder

class CommunityForm(forms.ModelForm):

    class Meta:
        model = Community
        fields = [
            "name",
            "ethnic_group",
            "county",
            "payam",
            "boma",
            "latitude",
            "longitude",
            "trust_score",
            "is_active",
        ]


class StakeholderForm(forms.ModelForm):

    class Meta:
        model = Stakeholder
        fields = [
            "stakeholder_type",
            "name",
            "designation",
            "organization",
            "email",
            "phone",
            "communities",
            "active",
        ]

