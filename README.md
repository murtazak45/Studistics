# Studistics - Study Partner Application

A web-based study partner application for college students built with Django.

## Project Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser (admin account):**
   ```bash
   python manage.py createsuperuser
   ```
   You'll be prompted to enter:
   - Username
   - Email
   - Password

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`

## Accessing the Application

- **Login Page:** `http://127.0.0.1:8000/login/`
- **Admin Panel:** `http://127.0.0.1:8000/admin/`
- **Logout:** `http://127.0.0.1:8000/logout/`

## Project Structure

```
studistics/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── db.sqlite3               # SQLite database
├── templates/               # HTML templates
│   └── login.html          # Login page (your custom template)
├── static/                  # Static files (CSS, JS, images)
└── studistics/              # Main project package
    ├── settings.py          # Django settings
    ├── urls.py              # URL routing configuration
    ├── auth_urls.py         # Authentication routes
    ├── views.py             # View functions
    ├── models.py            # Database models
    ├── admin.py             # Admin customization
    ├── apps.py              # App configuration
    ├── wsgi.py              # WSGI configuration
    └── __init__.py          # Package initialization
```

## Authentication System

- **Django's built-in authentication** is used for login/logout
- Login view renders your `login.html` template from `templates/` directory
- Users are redirected to home page after successful login
- Logout redirects back to login page

## Adding Your Login Template

1. Place your `login.html` file in the `templates/` directory
2. Ensure your form has:
   - Method: POST
   - Field name: `username`
   - Field name: `password`
   - CSRF token: `{% csrf_token %}`

### Example form structure:
```html
<form method="post">
    {% csrf_token %}
    <input type="text" name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
</form>
```

## Notes

- The application uses SQLite for database (suitable for development)
- Debug mode is enabled (change `DEBUG = False` in settings.py for production)
- Static files configuration is set up for both development and production
- Admin interface is available at `/admin/` (use superuser credentials)
