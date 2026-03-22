from django import forms
from django.core.exceptions import ValidationError
from .models import Subject, Topic, StudySession, Exam


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['subject', 'name', 'confidence_level', 'last_studied_date']
        widgets = {
            'last_studied_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'last_studied_date': 'Last Studied Date',
            'confidence_level': 'Confidence Level',
        }


class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = [
            'topic',
            'study_time',
            'confidence_level',
            'practice_score',
            'revision_count',
        ]
        widgets = {
            'study_time': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'practice_score': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '100'}),
        }
        labels = {
            'study_time': 'Study Time (hours)',
            'confidence_level': 'How confident do you feel?',
            'practice_score': 'Expected score out of 100 (if tested right now)',
            'revision_count': 'Number of times you revised this topic today',
        }

    def clean_study_time(self):
        study_time = self.cleaned_data.get('study_time')
        if study_time is not None and study_time <= 0:
            raise ValidationError('Study time must be greater than zero.')
        return study_time

    def clean_revision_count(self):
        revision_count = self.cleaned_data.get('revision_count')
        if revision_count is not None and revision_count < 0:
            raise ValidationError('Revision count cannot be negative.')
        return revision_count


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['subject', 'exam_name', 'exam_date']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'exam_name': 'Exam Name',
            'exam_date': 'Exam Date',
        }

    def clean_exam_date(self):
        from datetime import date
        exam_date = self.cleaned_data.get('exam_date')
        if exam_date and exam_date < date.today():
            raise ValidationError('Exam date cannot be in the past.')
        return exam_date
