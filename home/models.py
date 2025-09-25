# home/models.py (only the Company model shown — keep the rest of your file as-is)
from django.db import models
from django.contrib.auth.models import User

class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- NEW: owner field so each company can be assigned to a User (recruiter) ---
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
        help_text="The user who 'owns' / manages this company (a recruiter). Optional."
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)
