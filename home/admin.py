# home/admin.py
from django.contrib import admin
from .models import Company, Job, JobApplication


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'location', 'created_at']
    list_filter = ['created_at', 'owner']
    search_fields = ['name', 'location', 'owner__username']
    ordering = ['-created_at']
    fields = ('owner', 'name', 'description', 'website', 'location', 'logo', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'job_type', 'experience_level', 'is_active', 'created_at']
    list_filter = ['job_type', 'experience_level', 'is_active', 'created_at', 'company']
    search_fields = ['title', 'company__name', 'location', 'description']
    ordering = ['-created_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'posted_by')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'location', 'job_type', 'experience_level')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'applied_at']
    list_filter = ['status', 'applied_at', 'job__company']
    search_fields = ['applicant__username', 'applicant__email', 'job__title', 'job__company__name']
    ordering = ['-applied_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Application Info', {
            'fields': ('job', 'applicant', 'status')
        }),
        ('Application Materials', {
            'fields': ('cover_letter', 'resume')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['applied_at', 'updated_at']
