from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create a Profile for a new user, or update the name if it's an existing user.
    """
    if created:
        # If the new user is a superuser, assign the ADMINISTRATOR role.
        # Otherwise, the default 'JOB_SEEKER' role will be used.
        role_to_assign = Profile.Role.ADMINISTRATOR if instance.is_superuser else Profile.Role.JOB_SEEKER
        Profile.objects.create(user=instance, name=instance.username, role=role_to_assign)
    else:
        # This ensures that if a user's details (like username) are updated,
        # the profile is also saved. This is good practice.
        instance.profile.save()