from django import forms
from .models import Job, Company, JobApplication


class JobForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        """
        Accept a `user` kwarg and limit company choices:
         - staff -> all companies
         - non-staff -> companies owned by the user
         - unauthenticated -> no companies
        """
        super().__init__(*args, **kwargs)
        if 'company' in self.fields:
            if user and user.is_authenticated:
                if getattr(user, 'is_staff', False):
                    qs = Company.objects.all()
                else:
                    qs = Company.objects.filter(owner=user)
            else:
                qs = Company.objects.none()
            self.fields['company'].queryset = qs
            self.fields['company'].empty_label = "— Select company —"

    class Meta:
        model = Job
        fields = [
            'title', 'company', 'description', 'requirements',
            'location', 'job_type', 'experience_level',
            'salary_min', 'salary_max'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Software Engineer'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': "Describe the job..."}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': "List required skills..."}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. San Francisco, CA or Remote'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80000'}),
        }
        labels = {
            'salary_min': 'Minimum Salary ($)',
            'salary_max': 'Maximum Salary ($)',
        }


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': "Write a compelling cover letter..."
            }),
            'resume': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }
        labels = {
            'cover_letter': 'Cover Letter',
            'resume': 'Resume (PDF, DOC, DOCX)',
        }
