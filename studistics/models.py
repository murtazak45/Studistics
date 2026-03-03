"""
Models for studistics app.
"""
from django.db import models
from django.contrib.auth.models import User


class Subject(models.Model):
    """Subject model to store academic subjects for each user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Topic(models.Model):
    """Topic model to store topics within subjects."""
    CONFIDENCE_CHOICES = [
        ('Weak', 'Weak'),
        ('Moderate', 'Moderate'),
        ('Strong', 'Strong'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES, default='Moderate')
    last_studied_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.subject.name})"
    
    @property
    def confidence(self):
        """Alias for confidence_level for template compatibility."""
        return self.confidence_level
