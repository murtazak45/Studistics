"""
Views for studistics app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import PasswordResetView
from .forms import SubjectForm, TopicForm
from .models import Subject, Topic
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """
    Handle user signup.
    GET: Render signup form
    POST: Process signup form and create user
    """
    if request.user.is_authenticated:
        # Redirect already logged-in users to dashboard
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')
        
        # Validation
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
        
        # Check if username already exists (use email as username)
        if email and User.objects.filter(username=email).exists():
            errors.append('This email is already registered.')
        
        if errors:
            # Render form with errors
            context = {
                'errors': errors,
                'name': name,
                'email': email,
            }
            return render(request, 'signup.html', context)
        
        # Create user
        try:
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                first_name=name.split()[0] if name else '',  # First word as first name
                last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',  # Rest as last name
                password=password
            )
            # Authenticate and log the user in immediately
            authenticated_user = authenticate(request, username=email, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                return redirect('dashboard')
            else:
                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')
        
        except Exception as e:
            context = {
                'errors': [f'An error occurred: {str(e)}'],
                'name': name,
                'email': email,
            }
            return render(request, 'signup.html', context)
    
    # GET request - render empty signup form
    return render(request, 'signup.html')


def home_view(request):
    """
    Home view - landing page.
    Redirects authenticated users to dashboard, shows landing page to others.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required(login_url='login')
def dashboard_view(request):
    """Dashboard view - shows user's subjects and topics."""
    subjects = Subject.objects.filter(user=request.user)
    topics = Topic.objects.filter(subject__user=request.user)
    
    context = {
        'subjects': subjects,
        'topics': topics,
    }
    return render(request, 'dashboard.html', context)


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with logging and proper redirect."""
    
    def form_valid(self, form):
        """Log when password reset email is sent."""
        email = form.cleaned_data['email']
        logger.info(f"Password reset requested for email: {email}")
        print(f"\n{'='*60}")
        print(f"[PASSWORD RESET] Email requested: {email}")
        print(f"[PASSWORD RESET] Email will be sent from: {form.cleaned_data.get('email')}")
        print(f"[EMAIL BACKEND] Using: smtp.gmail.com")
        print(f"[EMAIL CONFIG] Emails are being sent via Gmail SMTP")
        print(f"{'='*60}\n")
        return super().form_valid(form)


@login_required(login_url='login')
def add_subject(request):
    """View to add a new subject."""
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.user = request.user
            subject.save()
            messages.success(request, f"Subject '{subject.name}' added successfully!")
            return redirect('dashboard')
    else:
        form = SubjectForm()

    return render(request, "add_subject.html", {"form": form})


@login_required(login_url='login')
def add_topic(request):
    """View to add a new topic."""
    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            if topic.subject.user == request.user:
                topic.save()
                messages.success(request, f"Topic '{topic.name}' added successfully!")
                return redirect('dashboard')
            else:
                messages.error(request, "You don't have permission to add topics to this subject.")
    else:
        form = TopicForm()
        form.fields['subject'].queryset = Subject.objects.filter(user=request.user)

    return render(request, "add_topic.html", {"form": form})