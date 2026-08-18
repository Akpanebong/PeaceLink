from django.core.mail import send_mail
from django.utils import timezone


def queue_agreement_notice(notice):
    notice.delivery_status = "queued"
    notice.sent_at = timezone.now()
    notice.save(update_fields=["delivery_status", "sent_at", "updated_at"])
    if notice.channel == "email" and "@" in notice.destination:
        send_mail(
            subject=f"PeaceLink agreement notice: {notice.agreement.agreement_id}",
            message=f"Agreement {notice.agreement.agreement_id} has been registered for monitoring.",
            from_email=None,
            recipient_list=[notice.destination],
            fail_silently=True,
        )
