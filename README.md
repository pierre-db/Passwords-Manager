# Django Password Manager

This is a Django re-implementation of the original PHP password manager, maintaining the same functionality while adding SQLite encryption.

## Features

- Time-based authentication (10-minute validity like original)
- Encrypted password storage using Fernet encryption
- Original search functionality with autocomplete
- Request limiting (5 requests per session)
- Same UI/UX as original

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
   - Open http://127.0.0.1:8000/ in your browser
   - Login with the username and password you created

## How it works

### Authentication
- Uses Django's built-in user authentication system
- Session-based authentication with login/logout
- Each user has their own isolated password data

### Data Storage
- SQLite database with Fernet encryption for password data
- Categories and entries are stored separately like the original structure
- **User-specific encryption keys** derived from each user's password + unique salt
- User-specific data isolation - each user only sees their own passwords
- PBKDF2 key derivation with 100,000 iterations (OWASP recommended)

### Search Functionality
- Same autocomplete search as original
- Special character handling preserved
- 6 suggestion limit maintained

## File Structure

```
django/
├── password_manager/         # Django project settings
├── passwords/                # Main app
│   ├── models.py             # Database models with encryption
│   ├── views.py              # Views replicating PHP logic
│   ├── urls.py               # URL routing
│   ├── templates/            # HTML templates
│   └── management/           # Custom commands
│       └── commands/
│           └── import_passwords.py  # Data import script
└── db.sqlite3                # SQLite database (created after migrations)
```

## Security Features

- **User-specific encryption**: Each user's passwords are encrypted with a key derived from their own password
- **Unique salts**: Each user gets a unique 32-byte salt for key derivation
- **PBKDF2 key derivation**: 100,000 iterations using SHA-256
- **Fernet encryption**: AES 128 in CBC mode with authentication
- **Session security**: User passwords are temporarily stored in session for decryption
- **Data isolation**: Users can only access their own encrypted data

## Notes

- The database file `db.sqlite3` will be created automatically
- Password data is encrypted per-user - if a user forgets their password, their data cannot be recovered
- The original INI file structure is preserved in the database
- JavaScript functionality is identical to the original
- Backward compatibility included for any data encrypted with the old global key system