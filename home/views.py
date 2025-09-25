# home/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

# IMPORTANT: job-related models & forms live in the `jobs` app in your project.
# We import Job, Company, JobApplication from jobs.models and forms from jobs.forms
from jobs.models import Job, Company, JobApplication
from jobs.forms import JobApplicationForm, JobForm


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
        user_has_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()

    context = {"job": job, "user_has_applied": user_has_applied}

    return render(request, "home/job_detail.html", context)


@login_required
def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)

    # Check if user has already applied
    existing_application = JobApplication.objects.filter(job=job, applicant=request.user).first()

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
            messages.success(request, "Your application has been submitted successfully!")
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobApplicationForm()

    context = {"job": job, "form": form}

    return render(request, "home/apply_job.html", context)


@login_required
def post_job(request):
    """
    Show the Post Job form. Limit the company choices to companies owned by the current user.
    """
    # Use the Company model from jobs app (where owner is defined)
    # Only show companies owned by current user
    user_companies = Company.objects.filter(owner=request.user)

    if request.method == "POST":
        form = JobForm(request.POST)
        # set the company queryset to only the user's companies before validation/save
        if "company" in form.fields:
            form.fields["company"].queryset = user_companies

        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm()
        # ensure the company field only lists companies owned by this user
        if "company" in form.fields:
            form.fields["company"].queryset = user_companies

    context = {"form": form, "companies": user_companies}
    return render(request, "home/post_job.html", context)


@login_required
def my_applications(request):
    applications = JobApplication.objects.filter(applicant=request.user)

    context = {"applications": applications}

    return render(request, "home/my_applications.html", context)
