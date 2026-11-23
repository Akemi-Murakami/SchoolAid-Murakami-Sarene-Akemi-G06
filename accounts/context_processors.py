from django.urls import reverse

from .models import Role

# (label, url name). A url name of None means the feature arrives in a later phase.
SHARED_END = [("Safety information", None), ("Emergency contacts", None), ("My profile", "profile")]

NAV = {
    Role.ADMIN: [
        ("Dashboard", "dashboard"),
        ("Emergency reports", None),
        ("Verification", None),
        ("Announcements", None),
        ("Incident history", None),
        ("Safety information", None),
        ("Emergency contacts", None),
        ("My profile", "profile"),
    ],
    Role.STUDENT: [("Dashboard", "dashboard"), ("Report an emergency", None), ("My reports", None)] + SHARED_END,
    Role.TEACHER: [("Dashboard", "dashboard"), ("Report an emergency", None), ("My reports", None)] + SHARED_END,
    Role.NURSE: [("Dashboard", "dashboard"), ("Medical reports", None), ("Notifications", None)] + SHARED_END,
    Role.SECURITY: [("Dashboard", "dashboard"), ("Security reports", None), ("Notifications", None)] + SHARED_END,
    Role.PARENT: [("Dashboard", "dashboard"), ("Announcements", None)] + SHARED_END,
}

PROFILE_PAGES = {"profile", "profile_edit", "password_change"}


def navigation(request):
    """Give every template the sidebar items that fit the user's role."""
    user = request.user
    if not user.is_authenticated:
        return {}
    current = request.resolver_match.url_name if request.resolver_match else ""
    items = []
    for label, name in NAV[user.role.role_name]:
        if name == "dashboard":
            active = current in {"dashboard", user.dashboard_url_name}
        elif name == "profile":
            active = current in PROFILE_PAGES
        else:
            active = False
        items.append({"label": label, "url": reverse(name) if name else None, "active": active})
    return {"nav_items": items}
