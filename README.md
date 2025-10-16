# Django Password Manager

A secure, modern password manager built with Django, featuring encrypted storage and a user-friendly admin interface. This is a complete rewrite of the original PHP application with significant security improvements.

## Features

### Core Functionality
- **Multi-user support** with secure authentication
- **Encrypted password storage** using Fernet encryption (AES 128)
- **Django Admin interface** for easy password management
- **Category-based organization** of password entries
- **Search and filtering** capabilities
- **User data isolation** - users only see their own passwords

### Security Features
- **User-specific encryption** with unique salts per user
- **PBKDF2 key derivation** (100,000 iterations, OWASP recommended)
- **Session-based authentication** via Django framework
- **CSRF protection** and input validation
- **Configurable request limiting** (default: 5 requests per session)

## Setup Instructions

1. **Make sure you're in the django directory and have the virtual environment activated:**
   ```bash
   cd django
   source ~/.virtualenvs/perso_password/bin/activate
   ```

2. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create a user account:**
   ```bash
   python manage.py createsuperuser
   ```
   Enter your desired username, email, and password.

4. **Import existing password data:**
   ```bash
   `python manage.py import_passwords --file=../import/passwords.txt --username=YOUR_USERNAME`
   ```
   Replace `YOUR_USERNAME` with the username you created in step 3. You'll be prompted to enter your password for encryption.

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   - **Admin Interface**: http://127.0.0.1:8000/admin/ (recommended)
   - **Original Interface**: http://127.0.0.1:8000/ (legacy compatibility)
   - Login with the username and password you created

## Usage

### Admin Interface (Recommended)
The Django admin provides a modern, secure interface for password management:

1. **Navigate to**: http://127.0.0.1:8000/admin/
2. **Login** with your user credentials
3. **Manage Password Categories**: Create/organize password groups
4. **Manage Password Entries**: Add/edit/delete individual passwords
   - Enter service name, URL, username, and password
   - Passwords are automatically encrypted using your session credentials
   - View existing passwords with masked previews
5. **Search and Filter**: Use built-in Django admin search/filter capabilities

### Legacy Interface
The original PHP-style interface is available at http://127.0.0.1:8000/ for compatibility.

## How it Works

### Authentication & Security
- **Django Authentication**: Secure user management with password hashing
- **Session Management**: User credentials stored securely in session for encryption
- **Per-User Encryption**: Each user's data encrypted with their own derived key
- **Data Isolation**: Users can only access their own password entries

### Database Structure
- **PasswordCategory**: Organizes passwords into groups/categories
- **PasswordEntry**: Individual password records with encryption
- **UserEncryptionProfile**: Stores user-specific encryption salts
- **SQLite Backend**: Lightweight, file-based database with encryption

## Configuration

### Settings
You can customize the application behavior in `password_manager/settings.py`:

```python
# Password Manager settings
PASSWORD_MANAGER_REQUEST_LIMIT = 5  # Max requests per session (0 = unlimited)
```

### Environment Variables
- `DJANGO_SECRET_KEY`: Django secret key (auto-generated if not set)

## File Structure

```
django/
├── password_manager/         # Django project configuration
│   ├── settings.py           # Application settings & configuration
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI application entry point
├── passwords/                # Main password management app
│   ├── models.py             # Database models with encryption
│   ├── admin.py              # Django admin interface configuration
│   ├── views.py              # Views for legacy interface
│   ├── urls.py               # App-specific URL routing
│   ├── templates/            # HTML templates for legacy UI
│   └── management/           # Custom Django commands
│       └── commands/
│           └── import_passwords.py  # Data import from old format
└── db.sqlite3                # SQLite database (auto-created)
```

## Troubleshooting

### Common Issues
1. **Migration errors**: Run `python manage.py makemigrations` then `python manage.py migrate`
2. **Admin access**: Ensure you created a superuser with `python manage.py createsuperuser`
3. **Session expired**: Re-login through `/login/` if encryption fails in admin
4. **Import errors**: Ensure the old .ini file path is correct and accessible

### Development
- **Debug mode**: Set `DEBUG = True` in settings.py for development
- **Database reset**: Delete `db.sqlite3` and re-run migrations to start fresh
- **Logs**: Check console output for Django error messages