"""
URL configuration for studistics project.
"""
from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('add-subject/', views.SubjectCreateView.as_view(), name='add_subject'),
    path('edit-subject/<int:pk>/', views.SubjectUpdateView.as_view(), name='edit_subject'),
    path('delete-subject/<int:pk>/', views.SubjectDeleteView.as_view(), name='delete_subject'),
    path('add-topic/', views.TopicCreateView.as_view(), name='add_topic'),
    path('edit-topic/<int:pk>/', views.TopicUpdateView.as_view(), name='edit_topic'),
    path('delete-topic/<int:pk>/', views.TopicDeleteView.as_view(), name='delete_topic'),
    path('admin/', admin.site.urls),
    path('', include('studistics.auth_urls')),
]

