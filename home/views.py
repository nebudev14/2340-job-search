from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Job, Company, JobApplication
from .forms import JobApplicationForm, JobForm


def is_recruiter(user):
    """
    Check if the user is a recruiter OR a staff member.
    This is used by the @user_passes_test decorator.
    """
    if not user.is_authenticated:
        return False
    # Allow staff members (admins) to pass
    if user.is_staff:
        return True
    # Assumes a 'profile' related object with a 'role' attribute exists.
    return hasattr(user, "profile") and user.profile.role == "RECRUITER"


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


@login_required
def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)

    # Prevent recruiters from applying for jobs
    if hasattr(request.user, "profile") and request.user.profile.role == "RECRUITER":
        messages.error(request, "Recruiter accounts are not permitted to apply for jobs.")
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
        form = JobForm(request.POST, user=request.user) # Pass user to form
        if form.is_valid():
            new_company_name = form.cleaned_data.get("new_company_name")
            company = form.cleaned_data.get("company")

            # If a new company name was provided, create it
            if new_company_name and not company:
                company, created = Company.objects.get_or_create(
                    name=new_company_name,
                    defaults={'owner': request.user} # Assign current user as owner
                )

            job = form.save(commit=False)
            job.company = company # Assign the selected or newly created company
            job.posted_by = request.user # Set posted_by before saving
            job.save()
            messages.success(request, "Job posted successfully!")
            # The form's save_m2m() is not needed here as we don't have m2m fields
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm(user=request.user)

    # For debugging / template convenience include companies visible to this user
    if request.user.is_staff:
        visible_companies = Company.objects.all()
    else:
        visible_companies = Company.objects.filter(owner=request.user)

    context = {
        "form": form,
        "visible_companies": visible_companies,
    }

    return render(request, "home/post_job.html", context)


@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def my_jobs(request):
    """
    Displays a list of jobs. For recruiters, it shows only their own jobs.
    For admins/staff, it shows all jobs on the platform.
    """
    if request.user.is_staff:
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

    if request.method == 'POST':
        job_title = job.title
        job.delete()
        messages.success(request, f'The job "{job_title}" has been successfully deleted.')
        return redirect('my_jobs')

    return render(request, 'home/delete_job_confirmation.html', {'job': job})

@login_required
@user_passes_test(is_recruiter, login_url="home.index")
def view_job_applications(request, job_id):
    """
    Allows a recruiter to view all applications for a specific job they posted.
    """
    job = get_object_or_404(Job, pk=job_id)

    # Security check: ensure the user owns the job or is staff
    if job.posted_by != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to view applications for this job.")

    applications = job.applications.all().order_by('-applied_at')

    context = {
        'job': job,
        'applications': applications,
    }

    return render(request, 'home/view_job_applications.html', context)


@login_required
def my_applications(request):
    applications = JobApplication.objects.filter(applicant=request.user)

    context = {
        "applications": applications,
    }

    return render(request, "home/my_applications.html", context)
