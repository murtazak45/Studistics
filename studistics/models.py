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


class StudySession(models.Model):
    """Stores analytics data for study tracking."""
    CONFIDENCE_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Medium'),
        (4, 'High'),
        (5, 'Very High'),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='sessions')
    study_time = models.IntegerField(help_text='Minutes studied')
    confidence_level = models.IntegerField(choices=CONFIDENCE_CHOICES)
    marks_scored = models.FloatField(null=True, blank=True)
    revision_count = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic.name} - {self.date}"


class Exam(models.Model):
    """Stores upcoming exams."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    exam_name = models.CharField(max_length=200)
    exam_date = models.DateField()

    def __str__(self):
        return f"{self.exam_name} - {self.subject.name}"


class RevisionLog(models.Model):
    """Tracks topic revision history."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='revisions')
    revision_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic.name} - {self.revision_date}"
