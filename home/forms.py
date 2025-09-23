from django import forms
from .models import Job, Company, JobApplication


class JobForm(forms.ModelForm):
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
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the job role, responsibilities, and what you\'re looking for...'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List the required skills, experience, and qualifications...'}),
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
                'placeholder': 'Write a compelling cover letter explaining why you\'re the perfect fit for this role...'
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }
        labels = {
            'cover_letter': 'Cover Letter',
            'resume': 'Resume (PDF, DOC, DOCX)',
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'website', 'location', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class JobSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Job title, keywords, or company'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City, state, or remote'
        })
    )
    job_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Job Types')] + Job.JOB_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    experience_level = forms.ChoiceField(
        required=False,
        choices=[('', 'All Levels')] + Job.EXPERIENCE_LEVELS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    salary_range = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any Salary'),
            ('30-50', '$30k - $50k'),
            ('50-80', '$50k - $80k'),
            ('80-120', '$80k - $120k'),
            ('120+', '$120k+'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
