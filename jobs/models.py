# jobs/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="companies"
    )
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="jobs"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs_posted",   # <-- unique related_name to avoid clash
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"
    
class JobApplication(models.Model):
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_applications")
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"
