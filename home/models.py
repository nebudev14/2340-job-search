# home/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
import json


class Company(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='companies',
        null=True,
        blank=True,
        help_text="User who owns/manages this company (optional)"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='company_logos/', blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('remote', 'Remote'),
        ('internship', 'Internship'),
    ]

    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]

    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='full-time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='mid')
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    @property
    def salary_range(self):
        if self.salary_min and self.salary_max:
            return f"${self.salary_min//1000}k - ${self.salary_max//1000}k"
        elif self.salary_min:
            return f"${self.salary_min//1000}k+"
        return "Salary not specified"


class JobApplication(models.Model):
    class ApplicationStatus(models.TextChoices):
        NEW = 'NEW', _('New')
        SCREENING = 'SCREENING', _('Screening')
        INTERVIEW = 'INTERVIEW', _('Interview')
        OFFER = 'OFFER', _('Offer')
        HIRED = 'HIRED', _('Hired')
        REJECTED = 'REJECTED', _('Rejected')

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    note = models.TextField(
        blank=True,
        verbose_name="Tailored Note",
        help_text="A brief note to the recruiter explaining why you're a great fit for this role."
    )
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.NEW)
    applied_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['job', 'applicant']
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"


class SavedSearch(models.Model):
    """
    Model to store saved search criteria for recruiters to find job seekers.
    Allows recruiters to save their search parameters and get notified of new matches.
    """
    name = models.CharField(max_length=200, help_text="Name for this saved search")
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='saved_searches',
        help_text="The recruiter who created this search"
    )
    
    # Search criteria fields for job seekers
    skills_query = models.CharField(max_length=500, blank=True, help_text="Skills to search for (comma-separated)")
    location = models.CharField(max_length=200, blank=True, help_text="Location filter")
    experience_years = models.CharField(max_length=20, blank=True, help_text="Years of experience filter")
    education_level = models.CharField(max_length=100, blank=True, help_text="Education level filter")
    current_company = models.CharField(max_length=200, blank=True, help_text="Current company filter")
    
    # Notification settings
    is_active = models.BooleanField(default=True, help_text="Whether to send notifications for this search")
    last_notified = models.DateTimeField(null=True, blank=True, help_text="Last time notifications were sent")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'recruiter']  # Prevent duplicate names per recruiter
    
    def __str__(self):
        return f"{self.name} - {self.recruiter.username}"
    
    def get_search_criteria(self):
        """Return search criteria as a dictionary"""
        return {
            'skills': self.skills_query,
            'location': self.location,
            'experience_years': self.experience_years,
            'education_level': self.education_level,
            'current_company': self.current_company,
        }
    
    def get_matching_candidates(self):
        """Get job seekers that match this saved search criteria"""
        from accounts.models import Profile
        
        # Start with all job seeker profiles
        candidates = Profile.objects.filter(role=Profile.Role.JOB_SEEKER)
        
        # Filter by skills
        if self.skills_query:
            skills_list = [skill.strip().lower() for skill in self.skills_query.split(',') if skill.strip()]
            if skills_list:
                skill_query = Q()
                for skill in skills_list:
                    skill_query |= Q(skills__name__icontains=skill)
                candidates = candidates.filter(skill_query).distinct()
        
        # Filter by location (in bio or experience)
        if self.location:
            candidates = candidates.filter(
                Q(bio__icontains=self.location) |
                Q(experiences__company__icontains=self.location)
            ).distinct()
        
        # Filter by experience years (rough calculation based on experience entries)
        if self.experience_years:
            try:
                years = int(self.experience_years)
                # This is a simplified filter - in a real app you'd calculate actual years
                candidates = candidates.filter(experiences__isnull=False).distinct()
            except ValueError:
                pass
        
        # Filter by education level
        if self.education_level:
            candidates = candidates.filter(
                educations__degree__icontains=self.education_level
            ).distinct()
        
        # Filter by current company
        if self.current_company:
            candidates = candidates.filter(
                experiences__company__icontains=self.current_company,
                experiences__is_current=True
            ).distinct()
        
        return candidates.order_by('-user__date_joined')
    
    def get_new_matches_since_last_notification(self):
        """Get new job seekers that match this search since last notification"""
        matching_candidates = self.get_matching_candidates()
        
        if self.last_notified:
            matching_candidates = matching_candidates.filter(user__date_joined__gt=self.last_notified)
        
        return matching_candidates
