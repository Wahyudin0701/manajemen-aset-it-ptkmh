import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates or updates a superuser based on credentials in the .env file.'

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv('SUPERUSER_USERNAME')
        email = os.getenv('SUPERUSER_EMAIL', '')
        password = os.getenv('SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.ERROR('SUPERUSER_USERNAME and SUPERUSER_PASSWORD must be set in .env'))
            return

        user, created = User.objects.get_or_create(username=username)
        if created:
            user.email = email
            user.is_superuser = True
            user.is_staff = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully created new superuser: {username}'))
        else:
            user.email = email
            user.is_superuser = True
            user.is_staff = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated password and permissions for existing user: {username}'))
