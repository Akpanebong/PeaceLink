from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from core.models import Stakeholder
from core.models import Alert


def notify_referral(referral, request=None):

    case = referral.case
    stakeholder = referral.stakeholder

    title = (
        f"New conflict case referral — {case.case_id}"
    )
    community_a = referral.case.community_a
    community_b = referral.case.community_b

    message = (
        f"A conflict case concerning water access has been referred to your organization. "
        f"Please review the case and follow up by {referral.follow_up_date}\n\n"
        f"Case: {case.case_id}\n"
        f"Conflict type: "
        f"{case.get_conflict_type_display()}\n"
        f"Severity: "
        f"{case.get_severity_display()}\n\n"
        f"Reason for referral:\n"
        f"{referral.reason} \n\n"
        f"Communities involved:\n"
        f"{community_a} vs {community_b}"
    )

    action_url = reverse(
        "conflict_detail",
        kwargs={"pk": case.pk},
    )

    # =====================================================
    # 1. IN-APP ALERT
    # =====================================================

    if stakeholder:

        Alert.objects.create(
            title=title,
            message=message,
            level=Alert.Level.ACTION,
            assigned_to=None,
            action_url=action_url,
        )

    # =====================================================
    # 2. EMAIL
    # =====================================================

    if stakeholder.email:

        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[stakeholder.email],
            fail_silently=True,
        )

    # =====================================================
    # 3. SMS
    # =====================================================

    # if stakeholder.phone:
    #     send_referral_sms(
    #         stakeholder=stakeholder,
    #         referral=referral,
    #     )

    return True

