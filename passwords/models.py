from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class PasswordCategory(models.Model):
    """Represents a password category (like 'Afam', 'CSE Plaisir', etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']  # Each user can have unique category names

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class UserEncryptionProfile(models.Model):
    """Stores user-specific encryption data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='encryption_profile')
    salt = models.CharField(max_length=64)  # Unique salt for each user
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.salt:
            # Generate a unique salt for this user
            self.salt = base64.b64encode(os.urandom(32)).decode()
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create encryption profile for a user"""
        profile, created = cls.objects.get_or_create(user=user)
        return profile

    def derive_key_from_password(self, password):
        """Derive encryption key from user password and salt"""
        # Use PBKDF2 with the user's password and unique salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt.encode(),
            iterations=100000,  # OWASP recommended minimum
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key


class PasswordEntry(models.Model):
    """Represents a password entry within a category"""
    category = models.ForeignKey(PasswordCategory, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_entries')

    # Structured fields
    service_name = models.CharField(max_length=200, help_text="Name of the service/website")
    service_url = models.URLField(blank=True, help_text="Optional URL for the service/website")
    username = models.CharField(max_length=200, help_text="Username/email for the service")
    encrypted_password = models.TextField(help_text="Encrypted password")
    comments = models.TextField(blank=True, help_text="Optional additional notes or comments")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__name', 'service_name', 'username']

    def encrypt_password(self, password, user_password):
        """Encrypt a password using user-specific key"""
        if not user_password:
            raise ValueError("User password required for encryption")

        key = self._get_user_encryption_key(user_password)
        f = Fernet(key)
        encrypted_data = f.encrypt(password.encode())
        self.encrypted_password = base64.b64encode(encrypted_data).decode()

    def decrypt_password(self, user_password):
        """Decrypt password using user-specific key"""
        if not self.encrypted_password:
            return ""

        try:
            key = self._get_user_encryption_key(user_password)
            f = Fernet(key)
            encrypted_data = base64.b64decode(self.encrypted_password.encode())
            decrypted_data = f.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception:
            return ""

    def _get_user_encryption_key(self, user_password):
        """Generate user-specific encryption key"""
        profile = UserEncryptionProfile.get_or_create_for_user(self.user)
        return profile.derive_key_from_password(user_password)

    def __str__(self):
        return f"{self.service_name} ({self.username}) - {self.category.name}"


    def save(self, *args, **kwargs):
        """Ensure user is set when saving password entry"""
        if not self.user_id and self.category:
            self.user = self.category.user
        super().save(*args, **kwargs)
