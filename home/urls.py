from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home.index"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/apply/", views.apply_for_job, name="apply_for_job"),
    path("post-job/", views.post_job, name="post_job"),
    path("my-applications/", views.my_applications, name="my_applications"),
]
