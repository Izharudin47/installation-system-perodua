"""
Django management command to seed the database with default users.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

 
class Command(BaseCommand):
    help = 'Seed database with default users'

    def handle(self, *args, **options):
        # Use plain ASCII text to avoid Windows console encoding issues
        self.stdout.write('Seeding database...')
        
        # Create admin user
        admin_email = 'admin@demo.com'
        admin_password = 'admin123'
        
        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'username': admin_email,
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password(admin_password)
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created admin user: {admin_email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Admin user already exists: {admin_email}')
            )
        
        # Create installer user
        installer_email = 'installer@demo.com'
        installer_password = 'installer123'
        
        installer_user, created = User.objects.get_or_create(
            email=installer_email,
            defaults={
                'username': installer_email,
                'role': 'installer'
            }
        )
        
        if created:
            installer_user.set_password(installer_password)
            installer_user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created installer user: {installer_email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Installer user already exists: {installer_email}')
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Seeding completed'))
