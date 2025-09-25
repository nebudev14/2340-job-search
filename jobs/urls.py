from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("post/", views.job_create, name="post_job"),
    path("<int:pk>/", views.job_detail, name="job_detail"),
]
