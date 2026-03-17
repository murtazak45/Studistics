"""
Admin configuration for studistics app.
"""
from django.contrib import admin
from .models import Subject, Topic, StudySession, Exam, RevisionLog


admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(StudySession)
admin.site.register(Exam)
admin.site.register(RevisionLog)
