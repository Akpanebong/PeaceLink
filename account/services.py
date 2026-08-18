from django.contrib.auth.models import Group


def sync_profile_groups(profile):
    group, _ = Group.objects.get_or_create(name=profile.get_role_display())
    profile.groups.add(group)
