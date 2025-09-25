from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.template.loader import render_to_string
from django.forms import inlineformset_factory
from django.db import transaction
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


def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        print("Form submitted")
        print(form)
        if form.is_valid():
            print("Form is valid")
            with transaction.atomic():
                user = form.save()
                # The profile is created automatically by the post_save signal.
                # We just need to update fields from the form.
                user.profile.role = form.cleaned_data.get("role")

                # --- NEW: store recruiter email if role is RECRUITER ---
                if form.cleaned_data.get("role") == Profile.Role.RECRUITER:
                    user.profile.email = form.cleaned_data.get("email")
                else:
                    # optional: clear any previous value if switching away from recruiter
                    user.profile.email = ""

                user.profile.save()

            auth_login(request, user)  # log the user in
            return redirect("home.index")  # or wherever you want to redirect them
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
        # The is_valid() call on a formset correctly handles validation for all its forms,
        # including ignoring extra, empty forms.
        if profile_form.is_valid() and all(fs.is_valid() for fs in all_formsets):
            with transaction.atomic():
                # Save the main profile object
                profile_form.save()
                # Save all the related objects in the formsets
                for formset in all_formsets:
                    formset.save()

            return redirect("accounts.profile_view", username=request.user.username)
        # If any form or formset is invalid, Django will automatically add error messages
        # to the form/formset objects, and the page will be re-rendered to display those errors.

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
    models = {
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

    ModelClass = models.get(formset_name)
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
        # The object ID to delete is passed in the request body by HTMX
        object_id = request.GET.get("object_id")
        if object_id:
            try:
                # Ensure the object belongs to the current user's profile before deleting
                obj = get_object_or_404(
                    ModelClass, pk=object_id, profile=request.user.profile
                )
                obj.delete()
            except:
                # If object not found or doesn't belong to user, do nothing but don't error
                pass
        # Create a response that will be swapped into the DOM (and thus remove the element).
        response = HttpResponse(status=200)
        # Add a custom HTMX header to trigger a client-side event after the swap.
        response["HX-Trigger"] = f"formset-item-deleted-{formset_name}"
        return response

    return HttpResponseNotAllowed(["GET", "DELETE"])
