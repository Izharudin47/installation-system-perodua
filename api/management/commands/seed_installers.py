"""
Django management command to seed the database with dummy installer data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Installer

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with dummy installer data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding dummy installers...')
        
        # Dummy installer data - 5 installers
        installers_data = [
            {
                'email': 'ahmad.rahman@installer.com',
                'password': 'mesb1234',
                'company': 'Ahmad Electrical Services Sdn Bhd',
                'name': 'Ahmad Rahman',
                'phone': '+60123456789',
                'address': '123 Jalan Ampang, Taman Ampang',
                'city': 'Kuala Lumpur',
                'state': 'Selangor',
                'latitude': 3.1390,
                'longitude': 101.6869,
                'coverage': ['C1', 'C2'],
                'specialties': ['Residential Installation', 'Commercial EV Chargers'],
                'certifications': ['CIDB G7', 'ST Class A'],
                'availability': 'available',
                'compliance_data': {
                    'st': {'registered': True, 'class': 'CLASS A'},
                    'cidb': {'registered': True, 'grade': 'G7', 'category': 'CE'},
                    'sst': {'registered': True, 'number': 'SST001'}
                }
            },
            {
                'email': 'lim.seng@installer.com',
                'password': 'mesb1234',
                'company': 'Lim & Sons Electrical Works',
                'name': 'Lim Seng Keong',
                'phone': '+60198765432',
                'address': '456 Jalan Bukit Bintang',
                'city': 'Kuala Lumpur',
                'state': 'Kuala Lumpur',
                'latitude': 3.1489,
                'longitude': 101.7118,
                'coverage': ['C1'],
                'specialties': ['Wall-Mounted Chargers', 'Fast Charging Stations'],
                'certifications': ['CIDB G6', 'ST Class B'],
                'availability': 'available',
                'compliance_data': {
                    'st': {'registered': True, 'class': 'CLASS B'},
                    'cidb': {'registered': True, 'grade': 'G6', 'category': 'CE'},
                    'sst': {'registered': True, 'number': 'SST002'}
                }
            },
            {
                'email': 'kumar.electrical@installer.com',
                'password': 'mesb1234',
                'company': 'Kumar Electrical & Engineering',
                'name': 'Kumar Rajendran',
                'phone': '+60123456790',
                'address': '789 Jalan Tun Razak',
                'city': 'Kuala Lumpur',
                'state': 'Kuala Lumpur',
                'latitude': 3.1615,
                'longitude': 101.7175,
                'coverage': ['C2', 'Southern'],
                'specialties': ['Pedestal Installation', 'Industrial Chargers'],
                'certifications': ['CIDB G7', 'ST Class A', 'ISO 9001'],
                'availability': 'busy',
                'compliance_data': {
                    'st': {'registered': True, 'class': 'CLASS A'},
                    'cidb': {'registered': True, 'grade': 'G7', 'category': 'CE'},
                    'sst': {'registered': True, 'number': 'SST003'},
                    'insurance': {'hasInsurance': True}
                }
            },
            {
                'email': 'tan.evtech@installer.com',
                'password': 'mesb1234',
                'company': 'Tan EV Technology Solutions',
                'name': 'Tan Wei Ming',
                'phone': '+60198765433',
                'address': '321 Jalan Puchong',
                'city': 'Puchong',
                'state': 'Selangor',
                'latitude': 3.0449,
                'longitude': 101.6168,
                'coverage': ['C1', 'Southern'],
                'specialties': ['Smart Chargers', 'Network-Enabled Chargers'],
                'certifications': ['CIDB G6', 'ST Class B'],
                'availability': 'available',
                'compliance_data': {
                    'st': {'registered': True, 'class': 'CLASS B'},
                    'cidb': {'registered': True, 'grade': 'G6', 'category': 'CE'},
                    'sst': {'registered': True, 'number': 'SST004'}
                }
            },
            {
                'email': 'hassan.charger@installer.com',
                'password': 'mesb1234',
                'company': 'Hassan Charger Installation Services',
                'name': 'Hassan bin Abdullah',
                'phone': '+60123456791',
                'address': '654 Jalan Shah Alam',
                'city': 'Shah Alam',
                'state': 'Selangor',
                'latitude': 3.0738,
                'longitude': 101.5184,
                'coverage': ['C1', 'C2'],
                'specialties': ['Floor-Mounted Chargers', 'Public Charging Stations'],
                'certifications': ['CIDB G7', 'ST Class A'],
                'availability': 'available',
                'compliance_data': {
                    'st': {'registered': True, 'class': 'CLASS A'},
                    'cidb': {'registered': True, 'grade': 'G7', 'category': 'CE'},
                    'sst': {'registered': True, 'number': 'SST005'},
                    'insurance': {'hasInsurance': True},
                    'coi': {'hasCoiHistory': True}
                }
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for installer_data in installers_data:
            email = installer_data.pop('email')
            password = installer_data.pop('password')
            
            # Create or get user
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'role': 'installer',
                    'first_name': installer_data['name'].split()[0],
                    'last_name': ' '.join(installer_data['name'].split()[1:]) if len(installer_data['name'].split()) > 1 else ''
                }
            )
            
            # Always update password
            user.set_password(password)
            user.role = 'installer'
            user.save()
            
            # Create or update installer profile
            installer, installer_created = Installer.objects.get_or_create(
                user=user,
                defaults=installer_data
            )
            
            if not installer_created:
                # Update existing installer
                for key, value in installer_data.items():
                    setattr(installer, key, value)
                installer.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated installer: {installer.company} ({email})')
                )
            else:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created installer: {installer.company} ({email})')
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Seeding completed: {created_count} created, {updated_count} updated'
        ))

