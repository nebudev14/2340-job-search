from django import forms
from .models import Job, Company, JobApplication


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["note", "resume"]
        widgets = {
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "resume": forms.FileInput(attrs={"class": "form-control"})
        }


class JobForm(forms.ModelForm):
    # New field to allow creating a company on the fly
    new_company_name = forms.CharField(
        label="Or Create a New Company",
        required=False,
        help_text="If your company isn't in the list above, add it here.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Job
        fields = [
            "title", "company", "new_company_name", "description", "requirements",
            "location", "latitude", "longitude", "job_type", "experience_level", 
            "salary_min", "salary_max",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "requirements": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "job_type": forms.Select(attrs={"class": "form-select"}),
            "experience_level": forms.Select(attrs={"class": "form-select"}),
            "salary_min": forms.NumberInput(attrs={"class": "form-control"}),
            "salary_max": forms.NumberInput(attrs={"class": "form-control"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Limit company choices to those owned by the user, or all for staff
        if user:
            if user.is_staff:
                self.fields["company"].queryset = Company.objects.all()
            else:
                self.fields["company"].queryset = Company.objects.filter(owner=user)
        
        # Make the company field not required, as we can create a new one
        self.fields["company"].required = False

    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get("company")
        new_company_name = cleaned_data.get("new_company_name")

        if not company and not new_company_name:
            raise forms.ValidationError("You must either select an existing company or provide a new company name.")
        return cleaned_data