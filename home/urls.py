from django.urls import path
from . import views
from django.http import JsonResponse

urlpatterns = [
    path("", views.index, name="home.index"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/post/", views.post_job, name="post_job"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/edit/", views.edit_job, name="edit_job"),
    path("jobs/<int:job_id>/delete/", views.delete_job, name="delete_job"),
    path(
        "jobs/<int:job_id>/toggle-status/",
        views.toggle_job_status,
        name="toggle_job_status",
    ),
    path("jobs/<int:job_id>/apply/", views.apply_for_job, name="apply_for_job"),
    path(
        "jobs/<int:job_id>/applications/",
        views.view_job_applications,
        name="view_job_applications",
    ),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path('jobs/<int:job_id>/pipeline/', views.applicant_pipeline, name='applicant_pipeline'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('management/export/', views.admin_export_data, name='admin_export_data'),
    path('jobs/map/', views.job_map, name='job_map'),
    path('api/jobs-for-map/', views.jobs_for_map_api, name='jobs_for_map_api'),
]