class EnglishUI(dict):
    """English labels used by the shared application templates."""
    def __missing__(self, key):
        return key.replace("_", " ").title()


def peacelink_context(request):
    return {
        "APP_NAME": "PeaceLink Uganda",
        "APP_TAGLINE": "Connecting Communities. Rebuilding Trust. Sustaining Peace.",
        "UI": EnglishUI({
            "home": "Home", "trade": "Trade", "corridors": "Corridors",
            "routes": "Routes", "agreements": "Agreements", "resolve": "Resolve",
            "dashboard": "Dashboard", "intel": "Dashboard", "profile": "Profile",
            "sign_in": "Sign in", "sign_out": "Sign out", "notifications": "Notifications",
            "no_new_notifications": "No new notifications",
        }),
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
