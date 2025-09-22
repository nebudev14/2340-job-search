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
        # The 'role' will be set to the default 'JOB_SEEKER' from the model.
        # The role can be updated later if needed, for example, in the signup view.
        Profile.objects.create(user=instance, name=instance.username)
    # Optional: If you want the profile name to always match the username
    instance.profile.save()