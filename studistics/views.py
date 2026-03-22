"""
Views for studistics app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from .forms import SubjectForm, TopicForm, StudySessionForm, ExamForm
from .models import Subject, Topic, StudySession, Exam, RevisionLog
from studistics.utils.analysis import analyze_user_topics
from studistics.services.study_planner import generate_daily_plan
from studistics.services.analytics_service import (
    get_study_time_trend,
    get_confidence_trend,
    get_topic_strength_distribution,
)
from datetime import date, timedelta
import json
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """
    Handle user signup.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')
        
        errors = []
        
        if not name:
            errors.append('Please enter your full name.')
        
        if not email:
            errors.append('Please enter your email.')
        elif '@' not in email or '.' not in email:
            errors.append('Please enter a valid email format.')
        
        if not password:
            errors.append('Please enter a password.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if email and User.objects.filter(username=email).exists():
            errors.append('This email is already registered.')
        
        if errors:
            context = {'errors': errors, 'name': name, 'email': email}
            return render(request, 'signup.html', context)
        
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=name.split()[0] if name else '',
                last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                password=password
            )
            authenticated_user = authenticate(request, username=email, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                return redirect('dashboard')
            else:
                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')
        
        except Exception as e:
            context = {'errors': [f'An error occurred: {str(e)}'], 'name': name, 'email': email}
            return render(request, 'signup.html', context)
    
    return render(request, 'signup.html')


def home_view(request):
    """Landing page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required(login_url='login')
def dashboard_view(request):
    """Dashboard view - shows user's subjects, topics, and analytics."""
    subjects = Subject.objects.filter(user=request.user).prefetch_related('topics')
    # Optimize query with select_related and Max annotation
    topics = Topic.objects.filter(subject__user=request.user).select_related('subject').annotate(
        latest_revision_date=Max('revisions__revision_date')
    )

    # --- Topic Strength Analytics ---
    analysis = analyze_user_topics(request.user)

    # --- Upcoming Exams (future dates only) ---
    upcoming_exams = Exam.objects.filter(
        user=request.user,
        exam_date__gte=date.today(),
    ).select_related('subject').order_by('exam_date')

    # --- Revision Reminders (not revised in last 3 days) ---
    three_days_ago = date.today() - timedelta(days=3)
    revision_reminders = []
    for topic in topics:
        if topic.latest_revision_date is None or topic.latest_revision_date < three_days_ago:
            revision_reminders.append(topic)

    # --- Daily Study Plan ---
    daily_plan = generate_daily_plan(request.user)

    # --- Chart Data ---
    study_time_data = get_study_time_trend(request.user)
    confidence_data = get_confidence_trend(request.user)
    strength_data = get_topic_strength_distribution(request.user)

    context = {
        'subjects': subjects,
        'topics': topics,
        'weak_count': len(analysis['weak_topics']),
        'moderate_count': len(analysis['moderate_topics']),
        'strong_count': len(analysis['strong_topics']),
        'weak_topics': analysis['weak_topics'],
        'moderate_topics': analysis['moderate_topics'],
        'strong_topics': analysis['strong_topics'],
        'upcoming_exams': upcoming_exams,
        'revision_reminders': revision_reminders,
        'daily_plan': daily_plan,
        # Chart data (JSON-encoded for JS consumption)
        'study_time_labels': json.dumps(study_time_data['labels']),
        'study_time_values': json.dumps(study_time_data['values']),
        'confidence_labels': json.dumps(confidence_data['labels']),
        'confidence_values': json.dumps(confidence_data['values']),
        'strength_labels': json.dumps(strength_data['labels']),
        'strength_values': json.dumps(strength_data['values']),
    }
    return render(request, 'dashboard.html', context)


class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        email = form.cleaned_data['email']
        logger.info(f"Password reset requested for email: {email}")
        return super().form_valid(form)


# ==========================================
# CLASS-BASED VIEWS FOR CRUD CONSOLIDATION
# ==========================================

class TitleContextMixin:
    """Mixin to inject title context into generic template."""
    page_title = ""
    page_subtitle = ""
    submit_btn_text = "Save"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.page_title
        context['page_subtitle'] = self.page_subtitle
        context['submit_btn_text'] = self.submit_btn_text
        return context


class SubjectCreateView(LoginRequiredMixin, SuccessMessageMixin, TitleContextMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'form.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Subject '%(name)s' added successfully!"
    page_title = "Add New Subject"
    page_subtitle = "Create a new subject to organize your studies."
    submit_btn_text = "Add Subject"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, SuccessMessageMixin, TitleContextMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'form.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Subject '%(name)s' updated successfully!"
    page_title = "Edit Subject"
    submit_btn_text = "Save Changes"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class SubjectDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Subject
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Subject '%(name)s' deleted successfully!"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_type'] = 'subject'
        context['object_name'] = self.object.name
        return context


class TopicCreateView(LoginRequiredMixin, SuccessMessageMixin, TitleContextMixin, CreateView):
    model = Topic
    form_class = TopicForm
    template_name = 'form.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Topic '%(name)s' added successfully!"
    page_title = "Add New Topic"
    page_subtitle = "Create a new topic and track your confidence level."
    submit_btn_text = "Add Topic"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['subject'].queryset = Subject.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        if form.instance.subject.user != self.request.user:
            messages.error(self.request, "Permission denied.")
            return redirect('dashboard')
        return super().form_valid(form)


class TopicUpdateView(LoginRequiredMixin, SuccessMessageMixin, TitleContextMixin, UpdateView):
    model = Topic
    form_class = TopicForm
    template_name = 'form.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Topic '%(name)s' updated successfully!"
    page_title = "Edit Topic"
    submit_btn_text = "Save Changes"

    def get_queryset(self):
        return super().get_queryset().filter(subject__user=self.request.user)
        
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['subject'].queryset = Subject.objects.filter(user=self.request.user)
        return form


class TopicDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Topic
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Topic '%(name)s' deleted successfully!"

    def get_queryset(self):
        return super().get_queryset().filter(subject__user=self.request.user)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_type'] = 'topic'
        context['object_name'] = self.object.name
        return context


# ==========================================
# STUDY SESSION VIEWS
# ==========================================

class StudySessionCreateView(LoginRequiredMixin, SuccessMessageMixin, TitleContextMixin, CreateView):
    model = StudySession
    form_class = StudySessionForm
    template_name = 'form.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Study session logged successfully!"
    page_title = "Log Study Session"
    page_subtitle = "Record your study session to track progress and analytics."
    submit_btn_text = "Log Session"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['topic'].queryset = Topic.objects.filter(subject__user=self.request.user)
        return form


# ==========================================
# EXAM VIEWS
# ==========================================

class ExamCreateView(LoginRequiredMixin, SuccessMessageMixin, TitleContextMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'form.html'
    success_url = reverse_lazy('dashboard')
    success_message = "Exam '%(exam_name)s' added successfully!"
    page_title = "Add Exam"
    page_subtitle = "Schedule an upcoming exam to help prioritise your study plan."
    submit_btn_text = "Add Exam"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['subject'].queryset = Subject.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
