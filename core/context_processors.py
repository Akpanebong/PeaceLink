from core.translations import language_choices, ui_for


def peacelink_context(request):
    active_language = getattr(request, "peacelink_language", "en")
    return {
        "APP_NAME": "PeaceLink South Sudan",
        "APP_TAGLINE": "Connecting Communities. Rebuilding Trust. Sustaining Peace.",
        "ACTIVE_LANGUAGE": active_language,
        "UI": ui_for(active_language),
        "LANGUAGES": language_choices(),
    }


def notifications_context(request):
    notification_count = 0
    notifications = []
    if request.user.is_authenticated:
        user_alerts = request.user.alerts.filter(is_read=False)
        notification_count = user_alerts.count()
        notifications = user_alerts.select_related("community")[:5]
    return {
        "NOTIFICATION_COUNT": notification_count,
        "NOTIFICATIONS": notifications,
    }
