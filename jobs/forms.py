# jobs/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Job, Company


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        # Use all model fields to avoid "Unknown field" errors if model field names differ.
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        # Accept an optional `user` kwarg (pop it so ModelForm doesn't choke).
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Remove backend / auto-managed fields from the form if they exist.
        for auto_field in ("id", "pk", "posted_by", "created_at", "updated_at", "created", "updated"):
            if auto_field in self.fields:
                del self.fields[auto_field]

        # If the form includes a company field, limit choices to companies owned by `user`.
        if "company" in self.fields:
            if user and getattr(user, "is_authenticated", False):
                self.fields["company"].queryset = Company.objects.filter(owner=user)
            else:
                # anonymous or no user -> no companies selectable
                self.fields["company"].queryset = Company.objects.none()

            # friendly empty label where appropriate (only for ModelChoiceField)
            try:
                self.fields["company"].empty_label = "— Select company —"
            except Exception:
                pass

        # Add sensible bootstrap classes to widgets that don't already have them.
        for name, field in list(self.fields.items()):
            widget = field.widget
            if widget is None:
                continue
            cls = widget.attrs.get("class", "")
            # select widgets -> form-select, everything else -> form-control
            if widget.__class__.__name__.lower().find("select") >= 0:
                wanted = "form-select"
            else:
                wanted = "form-control"
            if wanted not in cls:
                widget.attrs["class"] = (cls + " " + wanted).strip()

    def clean(self):
        cleaned = super().clean()

        # If your model uses salary fields (salary_min / salary_max, or min_salary / max_salary),
        # try both naming patterns and validate min <= max if both exist.
        # This is defensive — it only runs if the fields are present.
        # Try salary_min / salary_max first:
        smin = cleaned.get("salary_min")
        smax = cleaned.get("salary_max")

        # fallback to min_salary / max_salary if first pair not present
        if smin is None and smax is None:
            smin = cleaned.get("min_salary")
            smax = cleaned.get("max_salary")

        if smin is not None and smax is not None:
            try:
                if float(smin) > float(smax):
                    # attach error to the min field if present, else to non-field errors
                    if "salary_min" in self.fields:
                        self.add_error("salary_min", "Minimum salary cannot be greater than maximum salary.")
                    elif "min_salary" in self.fields:
                        self.add_error("min_salary", "Minimum salary cannot be greater than maximum salary.")
                    else:
                        raise ValidationError("Minimum salary cannot be greater than maximum salary.")
            except (TypeError, ValueError):
                # if values cannot be compared as numbers, ignore here and let model/field validators handle it
                pass

        return cleaned
