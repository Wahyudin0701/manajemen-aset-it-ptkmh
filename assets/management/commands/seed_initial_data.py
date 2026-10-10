import os
from django.core.management.base import BaseCommand
from assets.models import Category

class Command(BaseCommand):
    help = 'Seeds initial default categories for the system'

    def handle(self, *args, **options):
        categories = ['Aset Karyawan', 'Aset Network']
        for cat_name in categories:
            cat, created = Category.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {cat_name}'))
                
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
