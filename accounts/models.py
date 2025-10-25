from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    class Role(models.TextChoices):
        JOB_SEEKER = "JOB_SEEKER", "Job Seeker"
        RECRUITER = "RECRUITER", "Recruiter"
        ADMINISTRATOR = "ADMINISTRATOR", "Administrator"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.JOB_SEEKER
    )
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class Skill(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="skills"
    )
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Education(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="educations"
    )
    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255, blank=True)
    field_of_study = models.CharField(max_length=255, blank=True)
    start_year = models.DateField(blank=True, null=True)
    end_year = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.school} - {self.degree}"


class Experience(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="experiences"
    )
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    start_year = models.DateField(blank=True, null=True)
    end_year = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} at {self.company}"


class Link(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="links")
    url = models.URLField(blank=True)
    label = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.label}: {self.url}"
