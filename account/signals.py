from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=Profile)
def sync_role_group(sender, instance, **kwargs):
    group_name = instance.get_role_display()
    group, _ = Group.objects.get_or_create(name=group_name)
    instance.groups.add(group)
