"""
URL configuration for studistics project.
"""
from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('add-subject/', views.add_subject, name='add_subject'),
    path('add-topic/', views.add_topic, name='add_topic'),
    path('admin/', admin.site.urls),
    path('', include('studistics.auth_urls')),
]

