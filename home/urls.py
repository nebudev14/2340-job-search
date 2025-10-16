from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home.index"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/post/", views.post_job, name="post_job"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/edit/", views.edit_job, name="edit_job"),
    path("jobs/<int:job_id>/delete/", views.delete_job, name="delete_job"),
    path("jobs/<int:job_id>/apply/", views.apply_for_job, name="apply_for_job"),
    path(
        "jobs/<int:job_id>/applications/",
        views.view_job_applications,
        name="view_job_applications",
    ),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path("my-applications/", views.my_applications, name="my_applications"),
]