from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    class Role(models.TextChoices):
        JOB_SEEKER = "JOB_SEEKER", "Job Seeker"
        RECRUITER = "RECRUITER", "Recruiter"
        ADMINISTRATOR = "ADMINISTRATOR", "Administrator"

    class SectionVisibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public (Visible to everyone)"
        RECRUITERS = "RECRUITERS", "Recruiters Only"
        PRIVATE = "PRIVATE", "Private (Only you can see it)"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.JOB_SEEKER
    )
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    resume = models.FileField(
        upload_to="user_resumes/", blank=True, null=True, help_text="Your default resume for one-click applications."
    )
    # Granular visibility settings for each profile section
    skills_visibility = models.CharField(
        max_length=20, choices=SectionVisibility.choices, default=SectionVisibility.RECRUITERS
    )
    education_visibility = models.CharField(
        max_length=20, choices=SectionVisibility.choices, default=SectionVisibility.RECRUITERS
    )
    experience_visibility = models.CharField(
        max_length=20, choices=SectionVisibility.choices, default=SectionVisibility.RECRUITERS
    )
    links_visibility = models.CharField(
        max_length=20, choices=SectionVisibility.choices, default=SectionVisibility.PUBLIC
    )
    resume_visibility = models.CharField(
        max_length=20, choices=SectionVisibility.choices, default=SectionVisibility.RECRUITERS,
        help_text="Controls visibility of the resume download link on your profile."
    )

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
