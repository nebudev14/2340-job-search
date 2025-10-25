from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='messaging.inbox'),
    path('compose/', views.compose, name='messaging.compose'),
    path('compose/<str:username>/', views.compose, name='messaging.compose_to'),
    path('conversation/<str:username>/', views.conversation, name='messaging.conversation'),
    path('delete/<int:message_id>/', views.delete_message, name='messaging.delete'),
]

