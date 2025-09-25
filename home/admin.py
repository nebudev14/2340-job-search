# home/admin.py
from django.contrib import admin
from .models import Company

# Try to import Job & JobApplication from jobs app if present.
# This avoids ImportError if those models live in jobs.models (or the jobs app isn't ready).
try:
    from jobs.models import Job, JobApplication
except Exception:
    Job = None
    JobApplication = None


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "website", "created_at")
    search_fields = ("name", "owner__username", "website")
    list_filter = ("owner",)
    readonly_fields = ("created_at",)


# Register Job and JobApplication (only if we successfully imported them)
if Job is not None:
    try:
        admin.site.register(Job)
    except Exception:
        # fail-safe: don't crash admin registration if shape differs
        pass

if JobApplication is not None:
    try:
        admin.site.register(JobApplication)
    except Exception:
        pass
