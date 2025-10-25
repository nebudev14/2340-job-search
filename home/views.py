from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.http import JsonResponse, HttpResponse
from accounts.models import Profile
import csv
from django.utils import timezone
from math import radians, sin, cos, sqrt, atan2
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Job, Company, JobApplication
from django.urls import reverse
from .forms import JobApplicationForm, JobForm


def is_recruiter(user):
    if not user.is_authenticated:
        return False
    # Allow staff members to pass
    if user.is_staff:
        return True
    # Assumes a 'profile' related object with a 'role' attribute exists.
    return hasattr(user, "profile") and user.profile.role in [
        Profile.Role.RECRUITER,
        Profile.Role.ADMINISTRATOR,
    ]


def index(request):
    # Get featured jobs (latest 3 active jobs)
    featured_jobs = Job.objects.filter(is_active=True)[:3]

    template_data = {
        "featured_jobs": featured_jobs,
    }
    return render(request, "home/index.html", {"template_data": template_data})


def job_list(request):
    jobs = Job.objects.filter(is_active=True)

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query)
            | Q(company__name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # Location filter
    location = request.GET.get("location", "")
    if location:
        jobs = jobs.filter(location__icontains=location)

    # Job type filter
    job_type = request.GET.get("job_type", "")
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    # Experience level filter
    experience_level = request.GET.get("experience_level", "")
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)

    # Salary range filter
    salary_range = request.GET.get("salary_range", "")
    if salary_range == "30-50":
        jobs = jobs.filter(salary_min__gte=30000, salary_max__lte=50000)
    elif salary_range == "50-80":
        jobs = jobs.filter(salary_min__gte=50000, salary_max__lte=80000)
    elif salary_range == "80-120":
        jobs = jobs.filter(salary_min__gte=80000, salary_max__lte=120000)
    elif salary_range == "120+":
        jobs = jobs.filter(salary_min__gte=120000)

    # Pagination
    paginator = Paginator(jobs, 10)  # Show 10 jobs per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "jobs": page_obj,
        "search_query": search_query,
        "location": location,
        "job_type": job_type,
        "experience_level": experience_level,
        "salary_range": salary_range,
        "job_types": Job.JOB_TYPES,
        "experience_levels": Job.EXPERIENCE_LEVELS,
    }

    return render(request, "home/job_list.html", context)


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    user_has_applied = False

    if request.user.is_authenticated:
        user_has_applied = JobApplication.objects.filter(
            job=job, applicant=request.user
        ).exists()

    context = {
        "job": job,
        "user_has_applied": user_has_applied,
    }

    return render(request, "home/job_detail.html", context)


def job_map(request):
    """
    Renders the interactive map page for viewing jobs.
    """
    return render(request, "home/job_map.html")


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth in miles.
    """
    R = 3958.8  # Radius of Earth in miles

    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def jobs_for_map_api(request):
    """
    API endpoint to provide job data for the interactive map.
    Can be filtered by distance if lat, lon, and distance (in miles) are provided.
    """
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    distance_miles = request.GET.get("distance")

    jobs = Job.objects.filter(
        is_active=True, latitude__isnull=False, longitude__isnull=False
    ).select_related("company")
    job_data = []

    for job in jobs:
        include_job = True
        # If distance filtering is active, check if the job is within range
        if lat and lon and distance_miles:
            try:
                user_lat, user_lon, max_dist = map(float, [lat, lon, distance_miles])
                job_dist = haversine(user_lat, user_lon, job.latitude, job.longitude)
                if job_dist > max_dist:
                    include_job = False
            except (ValueError, TypeError):
                # Ignore invalid filter parameters
                pass

        if include_job:
            job_data.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company.name,
                    "lat": job.latitude,
                    "lon": job.longitude,
                    "url": reverse("job_detail", args=[job.id]),
                }
            )

    return JsonResponse(job_data, safe=False)


@login_required
def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)

    # Prevent recruiters from applying for jobs
    if hasattr(request.user, "profile") and request.user.profile.role == "RECRUITER":
        messages.error(
            request, "Recruiter accounts are not permitted to apply for jobs."
        )
        return redirect("job_detail", job_id=job.id)

    # Check if user has already applied
    existing_application = JobApplication.objects.filter(
        job=job, applicant=request.user
    ).first()

    if existing_application:
        messages.warning(request, "You have already applied for this job.")
        return redirect("job_detail", job_id=job.id)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(
                request, "Your application has been submitted successfully!"
            )
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobApplicationForm()

    context = {
        "job": job,
        "form": form,
    }

    return render(request, "home/apply_job.html", context)


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def post_job(request):
    """
    Important: pass `user=request.user` into JobForm so the company select
    is limited to companies the current user owns (unless staff).
    """
    if request.method == "POST":
        form = JobForm(request.POST, user=request.user)  # Pass user to form
        if form.is_valid():
            new_company_name = form.cleaned_data.get("new_company_name")
            company = form.cleaned_data.get("company")

            # If a new company name was provided, create it
            if new_company_name and not company:
                company, created = Company.objects.get_or_create(
                    name=new_company_name,
                    defaults={"owner": request.user},  # Assign current user as owner
                )

            job = form.save(commit=False)
            job.company = company  # Assign the selected or newly created company
            job.posted_by = request.user  # Set posted_by before saving
            job.save()
            messages.success(request, "Job posted successfully!")
            # The form's save_m2m() is not needed here as we don't have m2m fields
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm(user=request.user)

    context = {
        "form": form,
    }

    return render(request, "home/post_job.html", context)


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def my_jobs(request):
    """
    Displays a list of jobs. For recruiters, it shows only their own jobs.
    For admins/staff, it shows all jobs on the platform.
    """
    if request.user.is_staff or (
        hasattr(request.user, "profile")
        and request.user.profile.role == Profile.Role.ADMINISTRATOR
    ):
        jobs = Job.objects.all().order_by("-created_at")
    else:
        jobs = Job.objects.filter(posted_by=request.user).order_by("-created_at")
    context = {
        "jobs": jobs,
    }
    return render(request, "home/my_jobs.html", context)


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def edit_job(request, job_id):
    """
    Allows a recruiter to edit a job they have posted.
    """
    job = get_object_or_404(Job, pk=job_id)

    # Security check: ensure the user owns the job or is staff
    if job.posted_by != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to edit this job.")

    if request.method == "POST":
        form = JobForm(request.POST, instance=job, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm(instance=job, user=request.user)

    return render(request, "home/edit_job.html", {"form": form, "job": job})


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def delete_job(request, job_id):
    """
    Allows a recruiter to delete a job they have posted after confirmation.
    """
    job = get_object_or_404(Job, pk=job_id)

    # Security check: ensure the user owns the job or is staff
    if job.posted_by != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to delete this job.")

    if request.method == "POST":
        job_title = job.title
        job.delete()
        messages.success(
            request, f'The job "{job_title}" has been successfully deleted.'
        )
        return redirect("my_jobs")

    return render(request, "home/delete_job_confirmation.html", {"job": job})


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def toggle_job_status(request, job_id):
    """
    Toggles the is_active status of a job posting.
    """
    job = get_object_or_404(Job, pk=job_id)

    # Security check: ensure the user owns the job or is staff
    if job.posted_by != request.user and not request.user.is_staff:
        return HttpResponseForbidden(
            "You are not allowed to change the status of this job."
        )

    if request.method == "POST":
        job.is_active = not job.is_active
        job.save()

        status_text = "activated" if job.is_active else "deactivated"
        messages.success(
            request, f'The job "{job.title}" has been successfully {status_text}.'
        )

    return redirect("my_jobs")


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def view_job_applications(request, job_id):
    """
    Allows a recruiter to view all applications for a specific job they posted.
    """
    job = get_object_or_404(Job, pk=job_id)

    # Security check: ensure the user owns the job or is staff
    if job.posted_by != request.user and not request.user.is_staff:
        return HttpResponseForbidden(
            "You are not allowed to view applications for this job."
        )

    applications = job.applications.all().order_by("-applied_at")

    context = {
        "job": job,
        "applications": applications,
    }

    return render(request, "home/view_job_applications.html", context)


@login_required
def my_applications(request):
    applications = JobApplication.objects.filter(applicant=request.user)

    context = {
        "applications": applications,
    }

    return render(request, "home/my_applications.html", context)


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def applicant_pipeline(request, job_id):
    """
    Displays a Kanban-style board for managing job applicants.
    """
    job = get_object_or_404(Job, pk=job_id)

    # Security check: ensure the user owns the job or is staff
    if job.posted_by != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to view this pipeline.")

    # Get all applications for the job, optimized with select_related
    applications = (
        job.applications.all()
        .select_related("applicant__profile")
        .order_by("-applied_at")
    )

    # Group applications by status
    applications_by_status = {
        stage[0]: [] for stage in JobApplication.ApplicationStatus.choices
    }
    for app in applications:
        # If the status is valid, add it to the correct list.
        # Otherwise, add it to the 'NEW' list as a fallback for old/invalid statuses.
        if app.status in applications_by_status:
            applications_by_status[app.status].append(app)
        else:
            applications_by_status[JobApplication.ApplicationStatus.NEW].append(app)

    # Structure data for the template to avoid needing a custom 'get_item' filter
    pipeline_stages_data = []
    for stage_key, stage_label in JobApplication.ApplicationStatus.choices:
        pipeline_stages_data.append(
            {
                "key": stage_key,
                "label": stage_label,
                "applications": applications_by_status.get(stage_key, []),
            }
        )
    context = {
        "job": job,
        "pipeline_stages": pipeline_stages_data,
        "status_choices": JobApplication.ApplicationStatus.choices,
    }
    return render(request, "home/applicant_pipeline.html", context)


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def update_application_status(request, application_id):
    """
    Updates the status of a job application. Handles both standard form posts and AJAX requests.
    """
    application = get_object_or_404(JobApplication, pk=application_id)
    job = application.job

    # Security check: ensure the user owns the job or is staff
    if job.posted_by != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to modify this application.")

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in JobApplication.ApplicationStatus.values:
            application.status = new_status
            application.save()
            message_text = f"Status for {application.applicant.username} updated to {application.get_status_display()}."

            # If this is an AJAX request (from drag-and-drop), return the message as JSON.
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"message": message_text})

            # For non-AJAX requests, use the standard Django messages framework.
            messages.success(request, message_text)
        elif request.headers.get("x-requested-with") == "XMLHttpRequest":
            # Handle invalid status for AJAX requests
            return JsonResponse({"error": "Invalid status"}, status=400)

    return redirect("applicant_pipeline", job_id=job.id)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url="home.index")
def admin_export_data(request):
    """
    Allows an administrator to select and export model data as a CSV file from the main site.
    """
    MODELS_TO_EXPORT = {
        "Jobs": Job,
        "Companies": Company,
        "Job Applications": JobApplication,
    }

    if request.method == "POST":
        model_key = request.POST.get("model_to_export")
        ModelClass = MODELS_TO_EXPORT.get(model_key)

        if not ModelClass:
            messages.error(request, "Invalid data type selected for export.")
            return redirect("admin_export_data")

        queryset = ModelClass.objects.all()
        meta = ModelClass._meta
        field_names = [
            field.name
            for field in meta.get_fields()
            if not field.many_to_many and not field.one_to_many
        ]

        response = HttpResponse(content_type="text/csv")
        filename = f"{meta.model_name}_export_{timezone.now().strftime('%Y-%m-%d')}.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        writer = csv.writer(response)

        writer.writerow(field_names)

        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)

        return response

    context = {"export_options": MODELS_TO_EXPORT.keys()}
    return render(request, "home/admin_export.html", context)
