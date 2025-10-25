from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.template.loader import render_to_string
from django.forms import inlineformset_factory
from django.db import transaction
from django.contrib import messages  # NEW: for success/error alerts

from accounts.forms import (
    BaseFormSet,
    CustomUserCreationForm,
    ProfileForm,
    SkillFormSet,
    EducationFormSet,
    ExperienceFormSet,
    LinkFormSet,
)
from accounts.models import Profile, Skill, Education, Experience, Link
from home.models import Job, JobApplication


def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # The profile is created automatically by the post_save signal.
                # We just need to update fields from the form.
                user.profile.role = form.cleaned_data.get("role")

                # Store recruiter email if recruiter
                if form.cleaned_data.get("role") == Profile.Role.RECRUITER:
                    user.profile.email = form.cleaned_data.get("email")
                else:
                    user.profile.email = ""

                user.profile.save()

            auth_login(request, user)  # log the user in
            return redirect("home.index")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("home.index")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect("home.index")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout(request):
    auth_logout(request)
    return redirect("home.index")


def profile_view(request, username):
    user_to_view = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user_to_view)

    return render(request, "accounts/profile_page.html", {"profile": profile})


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=profile)
        skill_formset = SkillFormSet(request.POST, instance=profile, prefix="skills")
        education_formset = EducationFormSet(
            request.POST, instance=profile, prefix="education"
        )
        experience_formset = ExperienceFormSet(
            request.POST, instance=profile, prefix="experience"
        )
        link_formset = LinkFormSet(request.POST, instance=profile, prefix="links")

        all_formsets = [
            skill_formset,
            education_formset,
            experience_formset,
            link_formset,
        ]

        if profile_form.is_valid() and all(fs.is_valid() for fs in all_formsets):
            with transaction.atomic():
                # Save the main profile object
                profile_form.save()
                # Save all the related objects in the formsets
                for formset in all_formsets:
                    formset.save()

            return redirect("accounts.profile_view", username=request.user.username)

    else:
        profile_form = ProfileForm(instance=profile)
        skill_formset = SkillFormSet(instance=profile, prefix="skills")
        education_formset = EducationFormSet(instance=profile, prefix="education")
        experience_formset = ExperienceFormSet(instance=profile, prefix="experience")
        link_formset = LinkFormSet(instance=profile, prefix="links")

    context = {
        "profile_form": profile_form,
        "skill_formset": skill_formset,
        "education_formset": education_formset,
        "experience_formset": experience_formset,
        "link_formset": link_formset,
    }
    return render(request, "accounts/edit_profile.html", context)


@login_required
def manage_form_rows(request, formset_name):
    # Mapping for models and factories to prevent unbound errors
    models_map = {
        "skills": Skill,
        "education": Education,
        "experience": Experience,
        "links": Link,
    }

    factories = {
        "skills": SkillFormSet,
        "education": EducationFormSet,
        "experience": ExperienceFormSet,
        "links": LinkFormSet,
    }

    ModelClass = models_map.get(formset_name)
    FormSetFactory = factories.get(formset_name)

    if not ModelClass or not FormSetFactory:
        return HttpResponse("", status=400)  # Invalid formset_name

    if request.method == "GET":  # Handle adding a new form
        # We don't need an instance, just the empty form structure
        formset = FormSetFactory(
            queryset=ModelClass.objects.none(), prefix=formset_name
        )
        context = {"form": formset.empty_form, "prefix": formset_name}
        html_content = render_to_string(
            "partials/form_row.html", context, request=request
        )
        return HttpResponse(html_content)

    if request.method == "DELETE":  # Handle deleting an item
        object_id = request.GET.get("object_id")
        if object_id:
            try:
                # Ensure the object belongs to the current user's profile before deleting
                obj = get_object_or_404(
                    ModelClass, pk=object_id, profile=request.user.profile
                )
                obj.delete()
            except:
                # Silently ignore if not found / unauthorized
                pass
        response = HttpResponse(status=200)
        response["HX-Trigger"] = f"formset-item-deleted-{formset_name}"
        return response

    return HttpResponseNotAllowed(["GET", "DELETE"])


# =========================
# Admin / Manage Users View
# =========================
def manage_users(request):
    """
    Admin dashboard:
    - Shows all users
    - Allows updating role
    - Allows deleting users
    Access control:
    - request.user must be superuser OR have profile.role == "ADMINISTRATOR"
    """

    # Access control check
    if not request.user.is_authenticated or (
        not request.user.is_superuser and request.user.profile.role != "ADMINISTRATOR"
    ):
        return redirect("home.index")

    # Get all profiles to show in the table
    users = (
        Profile.objects.select_related("user").all().order_by("role", "user__username")
    )

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")

        # Fetch the target profile we want to operate on
        target = get_object_or_404(Profile.objects.select_related("user"), id=user_id)

        # ---------- DELETE USER FLOW ----------
        if action == "delete":
            # Safety rules:
            # - You cannot delete yourself
            # - You cannot delete another ADMINISTRATOR
            if target.user == request.user:
                messages.error(request, "You cannot delete your own account.")
            elif target.role == "ADMINISTRATOR":
                messages.error(request, "You cannot delete another administrator.")
            else:
                username = target.user.username
                # Deleting the Django User will cascade and delete the Profile
                target.user.delete()
                messages.success(request, f"User '{username}' has been deleted.")
            return redirect("accounts.manage_users")

        # ---------- UPDATE ROLE FLOW ----------
        if action == "update":
            new_role = request.POST.get("new_role")

            # Allowed roles are any defined in Profile.Role.choices.
            valid_roles = [r[0] for r in Profile.Role.choices]
            if new_role in valid_roles and target.role != new_role:
                old_role = target.role

                # --- NEW: Clean up data from the user's OLD role ---
                # If they were a Job Seeker, delete their applications.
                if old_role == Profile.Role.JOB_SEEKER:
                    deleted_count, _ = JobApplication.objects.filter(
                        applicant=target.user
                    ).delete()
                    if deleted_count > 0:
                        messages.info(
                            request,
                            f"Cleared {deleted_count} job application(s) for {target.user.username}.",
                        )

                # If they were a Recruiter, delete their job postings.
                if old_role == Profile.Role.RECRUITER:
                    deleted_count, _ = Job.objects.filter(
                        posted_by=target.user
                    ).delete()
                    if deleted_count > 0:
                        messages.info(
                            request,
                            f"Cleared {deleted_count} job posting(s) for {target.user.username}.",
                        )

                target.role = new_role
                target.save()
                messages.success(
                    request,
                    f"{target.user.username}'s role updated to {target.get_role_display()}.",
                )
            elif new_role not in valid_roles:
                messages.error(request, "Invalid role selection.")
            return redirect("accounts.manage_users")

        # If somehow neither delete nor update:
        messages.error(request, "Unknown action.")
        return redirect("accounts.manage_users")

    # GET request: render the page
    return render(request, "accounts/manage_users.html", {"users": users})
