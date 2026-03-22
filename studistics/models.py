"""
Models for studistics app.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


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
    study_time = models.FloatField(
        help_text='Hours studied (e.g., 0.5, 1.5)',
        validators=[MinValueValidator(0.0)]
    )
    confidence_level = models.IntegerField(choices=CONFIDENCE_CHOICES)
    practice_score = models.FloatField(
        null=True, blank=True,
        help_text='Score as a percentage (0 to 100)',
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    revision_count = models.PositiveIntegerField(default=0)
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


@receiver([post_save, post_delete], sender=StudySession)
def update_topic_confidence(sender, instance, **kwargs):
    """Updates the Topic's confidence_level dynamically whenever a session is logged or removed."""
    from studistics.utils.analysis import calculate_topic_strength
    
    # Cascade deletes might remove the topic before this signal finishes
    if Topic.objects.filter(pk=instance.topic_id).exists():
        result = calculate_topic_strength(instance.topic)
        strength_title = result["strength"].capitalize()  # "Weak", "Moderate", "Strong"
        Topic.objects.filter(pk=instance.topic_id).update(confidence_level=strength_title)

