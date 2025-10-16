from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from passwords.models import PasswordCategory, PasswordEntry
import os
import re
import getpass


class Command(BaseCommand):
    help = 'Import passwords from a text file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to the text file to import',
            default='import/passwords.txt'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username to import passwords for',
            required=True
        )
        parser.add_argument(
            '--password',
            type=str,
            help='User password for encryption (will be prompted if not provided)',
        )

    def handle(self, *args, **options):
        ini_file = options['ini_file']
        username = options['username']
        password = options['password']

        # Get password if not provided
        if not password:
            password = getpass.getpass('Enter user password for encryption: ')

        # Get or create user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Found user: {username}')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User not found: {username}. Please create the user first.')
            )
            return

        # Construct absolute path
        if not os.path.isabs(ini_file):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ini_file = os.path.join(base_dir, ini_file)

        if not os.path.exists(ini_file):
            self.stdout.write(
                self.style.ERROR(f'INI file not found: {ini_file}')
            )
            return

        self.stdout.write(f'Importing from: {ini_file} for user: {username}')

        try:
            with open(ini_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Create or get the "personal" category for all entries
            personal_category, created = PasswordCategory.objects.get_or_create(
                user=user,
                name='personal'
            )
            if created:
                self.stdout.write('Created "personal" category')

            current_service_name = None
            current_data = []

            for line in lines:
                line = line.strip()

                # Check if this is a service line (ends with :)
                if re.match(r'.+:$', line):
                    # Save previous service if exists
                    if current_service_name and current_data:
                        self.save_service_data(current_service_name, current_data, user, password)

                    # Start new service
                    current_service_name = line[:-1]  # Remove the ':'
                    current_data = []

                elif line and current_service_name:
                    # Add data line to current service
                    current_data.append(line)

            # Save the last service
            if current_service_name and current_data:
                self.save_service_data(current_service_name, current_data, user, password)

            self.stdout.write(
                self.style.SUCCESS('Successfully imported password data with user-specific encryption')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing data: {e}')
            )

    def save_service_data(self, service_name, data_lines, user, password):
        """Save encrypted password data for a service"""
        # Parse data_lines into structured format
        # New format: [service_url (optional)], username, password, [comments]

        if len(data_lines) >= 2:
            # Check if first line looks like a URL
            service_url = ""
            username_index = 0

            if len(data_lines) >= 3 and ('.' in data_lines[0] or 'http' in data_lines[0].lower()):
                # First line is likely a URL
                service_url = data_lines[0]
                username_index = 1

            username = data_lines[username_index]
            password_value = data_lines[username_index + 1]
            comments = '\n'.join(data_lines[username_index + 2:]) if len(data_lines) > username_index + 2 else ""

            # Get the "personal" category
            personal_category = PasswordCategory.objects.get(user=user, name='personal')

            # Create new structured entry
            entry = PasswordEntry(
                category=personal_category,
                user=user,
                service_name=service_name,
                service_url=service_url,
                username=username,
                comments=comments
            )

            # Encrypt the password
            if password_value:
                entry.encrypt_password(password_value, password)

            entry.save()
            url_info = f" ({service_url})" if service_url else ""
            self.stdout.write(f'Created entry: {service_name}{url_info} - {username}')
        else:
            self.stdout.write(
                self.style.WARNING(f'Skipping {service_name} - insufficient data (need at least username and password)')
            )