# Makerere University — Student Hostel Management System

A complete Django web application for managing student hostel bookings at Makerere University.

## Features
- Student registration with email verification (MailerSend)
- Role-based access: Student, Hostel Manager, Admin
- Hostel & room listings with search and filters
- Online booking with approval workflow
- Email notifications (approval/rejection via MailerSend)
- Student medical records (admin-only access)
- Contact/feedback forms per hostel
- Admin dashboard with system-wide statistics
- Manager dashboard with booking management
- Responsive design (mobile-friendly)

## Tech Stack
- **Backend**: Django 4.2 LTS
- **Database**: SQLite
- **Frontend**: Django Templates, HTML5, CSS3, Vanilla JS
- **Email**: MailerSend HTTP API
- **Static Files**: WhiteNoise
- **Fonts**: Fraunces + Plus Jakarta Sans (Google Fonts)
- **Icons**: Font Awesome 6

---

## Quick Start (Local Development)

### 1. Clone / extract the project
```bash
cd hostel_system
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and set your SECRET_KEY and MailerSend credentials
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create sample data (optional)
```bash
python manage.py create_sample_data
```

### 7. Create superuser (if not using sample data)
```bash
python manage.py createsuperuser
```
Then update that user's role to 'admin' and set email_verified=True via Django admin.

### 8. Run the development server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

**Default sample accounts** (if you ran create_sample_data):
| Role    | Username  | Password      |
|---------|-----------|---------------|
| Admin   | admin     | Admin@1234    |
| Manager | manager1  | Manager@1234  |
| Student | student1  | Student@1234  |

---

## Deployment on PythonAnywhere

### 1. Clone the project
Open a Bash console in PythonAnywhere and clone your repository into your home directory:
```bash
git clone https://github.com/justinaerica97-maker/hostel.git hostel_system
```

### 2. Create virtual environment
```bash
python3.10 -m venv ~/venv
source ~/venv/bin/activate
pip install -r ~/hostel_system/requirements.txt
```

### 3. Configure .env
```bash
cd ~/hostel_system
cp .env.example .env
nano .env
```
Set:
- `SECRET_KEY` — a long random string
- `DEBUG=False`
- `ALLOWED_HOSTS=yourusername.pythonanywhere.com`
- `MAILERSEND_API_KEY` — your MailerSend API key
- `MAILERSEND_FROM_EMAIL` — your verified sender email
- `MAILERSEND_FROM_NAME=Makerere Hostels`

### 4. Run migrations and collect static files
```bash
cd ~/hostel_system
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py create_sample_data  # optional
```

### 5. Configure WSGI
In the PythonAnywhere Web tab, set the WSGI file to:
```python
import sys, os
path = '/home/yourusername/hostel_system'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 6. Web Tab Settings
- **Source code**: `/home/yourusername/hostel_system`
- **Working directory**: `/home/yourusername/hostel_system`
- **Virtualenv**: `/home/yourusername/venv`
- **Static files**:
  - URL: `/static/` → Directory: `/home/yourusername/hostel_system/staticfiles`
  - URL: `/media/` → Directory: `/home/yourusername/hostel_system/media`

### 7. Reload
Click **Reload** in the Web tab. Your app will be live!

---

## Project Structure
```
hostel_system/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── hostel_mgmt/
│   ├── models.py          # Data models
│   ├── views.py           # All views
│   ├── urls.py            # URL patterns
│   ├── forms.py           # Forms
│   ├── admin.py           # Admin configuration
│   ├── decorators.py      # Role-based access decorators
│   ├── email_utils.py     # MailerSend email functions
│   ├── static/
│   │   ├── css/main.css
│   │   └── js/main.js
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── registration/
│   │   ├── accounts/
│   │   ├── dashboard/
│   │   ├── hostels/
│   │   ├── bookings/
│   │   ├── feedback/
│   │   └── medical/
│   └── management/commands/
│       └── create_sample_data.py
├── requirements.txt
├── .env.example
└── manage.py
```

---

## Environment Variables
| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key (required) |
| `DEBUG` | `True` for dev, `False` for production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `MAILERSEND_API_KEY` | Your MailerSend API key |
| `MAILERSEND_FROM_EMAIL` | Verified sender email address |
| `MAILERSEND_FROM_NAME` | Display name for sent emails |

---

## MailerSend Setup
1. Register at [mailersend.com](https://mailersend.com)
2. Add and verify your sending domain
3. Generate an API key under **API Tokens**
4. Set `MAILERSEND_API_KEY` and `MAILERSEND_FROM_EMAIL` in `.env`

> **Note**: Without a MailerSend key, email sending is skipped silently. Use the Django admin to manually verify emails during development.
