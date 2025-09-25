from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Job, Company
from .forms import JobForm

def job_list(request):
    """
    Public list of jobs.
    """
    qs = Job.objects.select_related("company", "posted_by").all()
    return render(request, "jobs/job_list.html", {"jobs": qs})

def job_detail(request, pk):
    """
    Detail page for a single job.
    """
    job = get_object_or_404(Job.objects.select_related("company","posted_by"), pk=pk)
    return render(request, "jobs/job_detail.html", {"job": job})

@login_required
def job_create(request):
    """
    Create a new job. Company choices are filtered by user (inside the form).
    """
    if request.method == "POST":
        form = JobForm(request.POST, user=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            # If you have many-to-many or extra fields to save, do it here
            return redirect("jobs:job_detail", pk=job.pk)
    else:
        form = JobForm(user=request.user)

    return render(request, "jobs/job_form.html", {"form": form})
