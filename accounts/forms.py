from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Profile, Skill, Education, Experience, Link


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=Profile.Role.choices,
        widget=forms.HiddenInput(),  # We will render this manually in the template
        initial=Profile.Role.JOB_SEEKER,
        label="I am a...",
    )

    # Recruiter contact email (required only when role == RECRUITER; enforced in clean())
    email = forms.EmailField(
        required=False,
        label="Recruiter Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2")

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        email = cleaned.get("email")
        if role == Profile.Role.RECRUITER and not email:
            self.add_error("email", "Email is required for recruiter accounts.")
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "bio", "resume"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "resume": forms.FileInput(attrs={"class": "form-control"}),
        }


# Create a custom base formset to hide the DELETE checkbox
class BaseFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        # This class is no longer strictly necessary with can_delete=False,
        # but it's good practice to keep in case can_delete is re-enabled later.


# Define formsets for each related model
SkillFormSet = inlineformset_factory(
    Profile,
    Skill,
    fields=("name",),
    extra=0,
    can_delete=False,
    widgets={
        "name": forms.TextInput(attrs={"class": "form-control"}),
    },
)


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ["school", "degree", "field_of_study", "start_year", "end_year"]
        widgets = {
            "school": forms.TextInput(attrs={"class": "form-control"}),
            "degree": forms.TextInput(attrs={"class": "form-control"}),
            "field_of_study": forms.TextInput(attrs={"class": "form-control"}),
            "start_year": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_year": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


EducationFormSet = inlineformset_factory(
    Profile, Education, form=EducationForm, extra=0, can_delete=False
)


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = [
            "company",
            "title",
            "is_current",
            "description",
            "start_year",
            "end_year",
        ]
        widgets = {
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "start_year": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_year": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


ExperienceFormSet = inlineformset_factory(
    Profile, Experience, form=ExperienceForm, extra=0, can_delete=False
)

LinkFormSet = inlineformset_factory(
    Profile,
    Link,
    fields=("url", "label"),
    extra=0,
    can_delete=False,
    widgets={
        "url": forms.URLInput(attrs={"class": "form-control"}),
        "label": forms.TextInput(attrs={"class": "form-control"}),
    },
)
