# jobs/admin.py
from django.contrib import admin
from .models import Company, Job


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "website")
    search_fields = ("name", "owner__username")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "posted_by", "is_active", "created_at")
    list_filter = ("is_active", "company")
    search_fields = ("title", "company__name", "description")
    raw_id_fields = ("company", "posted_by")
