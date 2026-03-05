from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Location

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up initial locations and superuser for POTPass system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial POTPass data...')
        
        # Create initial locations
        locations_data = [
            {
                'name': 'Swahilipot Hub',
                'code': 'HUB',
                'is_active': True
            },
            {
                'name': 'Swahilipot FM',
                'code': 'FM',
                'is_active': True
            }
        ]
        
        created_locations = 0
        for loc_data in locations_data:
            location, created = Location.objects.get_or_create(
                code=loc_data['code'],
                defaults=loc_data
            )
            if created:
                created_locations += 1
                self.stdout.write(f'Created location: {location.name} ({location.code})')
            else:
                self.stdout.write(f'Location already exists: {location.name} ({location.code})')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            hub_location = Location.objects.get(code='HUB')
            superuser = User.objects.create_superuser(
                username='admin',
                email='admin@potpass.com',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                role='admin',
                assigned_location=hub_location
            )
            self.stdout.write(f'Created superuser: {superuser.username} assigned to {superuser.assigned_location.name}')
        else:
            self.stdout.write('Superuser already exists')
        
        self.stdout.write(self.style.SUCCESS(f'\nSetup complete! Created {created_locations} locations.'))
        self.stdout.write('You can now login with:')
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('  Location: Swahilipot Hub')
        self.stdout.write('\nPlease change the password after first login!')
