from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse

from core.models import Alert


def notify_trade_connection(connection, request=None):
    offer = connection.offer
    requester = connection.requester
    owner = offer.owner
    requester_name = requester.get_full_name() or requester.username
    title = f"{requester_name} connected to {offer.commodity}"
    message = (
        f"{requester_name} connected to your trade offer. "
        f"Phone: {requester.phone or 'not provided'}. Email: {requester.email or 'not provided'}."
    )
    url = reverse("trade_detail", kwargs={"pk": offer.pk})
    absolute_url = request.build_absolute_uri(url) if request else url

    Alert.objects.create(title=title, message=message, assigned_to=owner, community=offer.community, action_url=url)

    if owner.email:
        send_mail(
            subject=title,
            message=f"{message}\n\nOpen PeaceLink: {absolute_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner.email],
            fail_silently=True,
        )

    if owner.phone:
        Alert.objects.create(
            title=f"SMS queued: {title}",
            message=f"SMS notification for {owner.phone}: {message}",
            assigned_to=owner,
            community=offer.community,
            action_url=url,
        )

    admin_users = get_user_model().objects.filter(is_staff=True, is_active=True).exclude(pk=owner.pk)
    for admin in admin_users:
        Alert.objects.create(title=title, message=message, assigned_to=admin, community=offer.community, action_url=url)
