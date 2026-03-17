from django import forms
from django.core.exceptions import ValidationError
from .models import Subject, Topic, StudySession


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['subject', 'name', 'confidence_level', 'last_studied_date']


class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = [
            'topic',
            'study_time',
            'confidence_level',
            'marks_scored',
            'revision_count',
        ]

    def clean_study_time(self):
        study_time = self.cleaned_data.get('study_time')
        if study_time is not None and study_time <= 0:
            raise ValidationError('Study time must be a positive number.')
        return study_time

    def clean_revision_count(self):
        revision_count = self.cleaned_data.get('revision_count')
        if revision_count is not None and revision_count < 0:
            raise ValidationError('Revision count cannot be negative.')
        return revision_count
