"""
Management command to seed test data for issues and mortality tracking.
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User

from farms.models import Farm, Flock, MortalityRecord, Breed
from houses.models import House
from issues.models import Issue, IssueComment


class Command(BaseCommand):
    help = 'Seed test data for issues and mortality tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing issues and mortality records before seeding',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of mortality data to generate (default: 30)',
        )

    def handle(self, *args, **options):
        clear = options['clear']
        days = options['days']

        if clear:
            self.stdout.write('Clearing existing issues and mortality records...')
            Issue.objects.all().delete()
            MortalityRecord.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return

        # Get houses with flocks
        houses = House.objects.all()
        if not houses.exists():
            self.stdout.write(self.style.ERROR('No houses found. Please run seed_data first.'))
            return

        self.stdout.write(f'Found {houses.count()} houses')

        # Ensure flocks exist for houses
        self.ensure_flocks(houses, admin_user)

        # Seed mortality records
        self.seed_mortality_records(houses, admin_user, days)

        # Seed issues
        self.seed_issues(houses, admin_user)

        self.stdout.write(self.style.SUCCESS('Successfully seeded issues and mortality data'))

    def ensure_flocks(self, houses, user):
        """Ensure each house has at least one active flock"""
        self.stdout.write('Ensuring flocks exist for houses...')
        
        # Get or create a default breed
        breed, created = Breed.objects.get_or_create(
            code='ROSS308',
            defaults={
                'name': 'Ross 308',
                'description': 'Fast-growing broiler breed',
                'average_weight_gain_per_week': 450,
                'average_feed_conversion_ratio': 1.7,
                'average_mortality_rate': 3.5,
                'typical_harvest_age_days': 42,
                'typical_harvest_weight_grams': 2500,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'  Created breed: {breed.name}')
        
        flocks_created = 0
        today = timezone.now().date()
        
        for house in houses:
            # Check if house has an active flock
            existing_flock = Flock.objects.filter(house=house, is_active=True).first()
            if existing_flock:
                continue
            
            # Create a new flock for this house
            # Random arrival date between 5 and 35 days ago
            days_ago = random.randint(5, 35)
            arrival_date = today - timedelta(days=days_ago)
            
            initial_count = random.randint(18000, 25000)
            
            flock = Flock.objects.create(
                house=house,
                breed=breed,
                batch_number=f'B{house.farm.id:02d}{house.house_number:02d}{timezone.now().strftime("%m%y")}',
                flock_code=f'FL-{house.id}-{timezone.now().strftime("%Y%m%d")}',
                arrival_date=arrival_date,
                start_date=arrival_date,
                expected_harvest_date=arrival_date + timedelta(days=42),
                initial_chicken_count=initial_count,
                current_chicken_count=initial_count - random.randint(50, 300),  # Some mortality
                status='growing',
                is_active=True,
                supplier='Default Supplier',
                notes='Auto-generated flock for testing',
                created_by=user,
            )
            flocks_created += 1
            self.stdout.write(f'  Created flock {flock.flock_code} for House {house.house_number}')
        
        self.stdout.write(self.style.SUCCESS(f'  Created {flocks_created} new flocks'))

    def seed_mortality_records(self, houses, user, days):
        """Create mortality records for flocks"""
        self.stdout.write('Seeding mortality records...')
        
        records_created = 0
        today = timezone.now().date()

        for house in houses:
            # Get active flock for this house
            flock = Flock.objects.filter(
                house=house,
                is_active=True
            ).first()

            if not flock:
                # Try to get any flock
                flock = Flock.objects.filter(house=house).first()

            if not flock:
                self.stdout.write(f'  No flock for House {house.house_number}, skipping mortality')
                continue

            # Generate mortality records for the past X days
            for day_offset in range(days):
                record_date = today - timedelta(days=day_offset)
                
                # Skip if record already exists
                if MortalityRecord.objects.filter(flock=flock, record_date=record_date).exists():
                    continue

                # Random mortality (0-10 per day, with some days having 0)
                if random.random() < 0.3:  # 30% chance of no mortality
                    continue

                total_deaths = random.randint(1, 10)
                
                # Optional breakdown
                has_breakdown = random.random() < 0.5  # 50% chance
                
                record_data = {
                    'flock': flock,
                    'house': house,
                    'record_date': record_date,
                    'total_deaths': total_deaths,
                    'recorded_by': user,
                }
                
                if has_breakdown:
                    # Distribute deaths across causes
                    remaining = total_deaths
                    causes = ['disease_deaths', 'culling_deaths', 'accident_deaths', 
                              'heat_stress_deaths', 'cold_stress_deaths', 'unknown_deaths']
                    
                    for cause in causes[:-1]:
                        if remaining > 0:
                            amount = random.randint(0, remaining)
                            record_data[cause] = amount
                            remaining -= amount
                    
                    record_data['unknown_deaths'] = remaining

                MortalityRecord.objects.create(**record_data)
                records_created += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {records_created} mortality records'))

    def seed_issues(self, houses, user):
        """Create sample issues for houses"""
        self.stdout.write('Seeding issues...')
        
        issues_created = 0
        
        # Sample issues data
        sample_issues = [
            {
                'category': 'equipment',
                'title': 'Feeder line malfunction',
                'description': 'The feeder line in section A is not dispensing feed properly. Birds are crowding at other feeders.',
                'priority': 'high',
                'location_in_house': 'Section A, Feeder line 1',
            },
            {
                'category': 'equipment',
                'title': 'Water nipple leaking',
                'description': 'Water nipple is leaking and creating wet spots on the litter.',
                'priority': 'medium',
                'location_in_house': 'Row 3, Nipple #15',
            },
            {
                'category': 'health',
                'title': 'Birds showing respiratory symptoms',
                'description': 'Several birds in the south corner are showing signs of respiratory distress. Sneezing and wheezing observed.',
                'priority': 'critical',
                'location_in_house': 'South corner',
            },
            {
                'category': 'health',
                'title': 'Leg weakness observed',
                'description': 'A few birds are showing difficulty walking. May need to increase vitamin D supplementation.',
                'priority': 'medium',
                'location_in_house': 'General',
            },
            {
                'category': 'environment',
                'title': 'Hot spot near heater',
                'description': 'Temperature sensor showing abnormally high readings near heater unit 2.',
                'priority': 'high',
                'location_in_house': 'Near heater unit 2',
            },
            {
                'category': 'environment',
                'title': 'Ammonia smell detected',
                'description': 'Strong ammonia smell in the house. Ventilation may need adjustment.',
                'priority': 'high',
                'location_in_house': 'General',
            },
            {
                'category': 'maintenance',
                'title': 'Light bulb replacement needed',
                'description': 'Two light bulbs are out in section B, creating dark spots.',
                'priority': 'low',
                'location_in_house': 'Section B',
            },
            {
                'category': 'maintenance',
                'title': 'Door seal damaged',
                'description': 'The seal on the main entrance door is damaged, allowing drafts.',
                'priority': 'medium',
                'location_in_house': 'Main entrance',
            },
            {
                'category': 'other',
                'title': 'Unusual bird behavior',
                'description': 'Birds are clustering unusually in one area. No obvious cause identified.',
                'priority': 'medium',
                'location_in_house': 'Center of house',
            },
        ]

        # Sample comments
        sample_comments = [
            "I'll check this out during my next round.",
            "This has been an ongoing issue. We should schedule a repair.",
            "Contacted the maintenance team about this.",
            "Situation seems to be improving after adjustments.",
            "Need to order replacement parts.",
        ]

        statuses = ['open', 'in_progress', 'resolved', 'closed']

        for house in houses[:5]:  # Create issues for first 5 houses
            # Create 2-4 issues per house
            num_issues = random.randint(2, 4)
            
            for _ in range(num_issues):
                issue_data = random.choice(sample_issues).copy()
                
                # Randomize status
                status = random.choice(statuses)
                
                issue = Issue.objects.create(
                    house=house,
                    title=issue_data['title'],
                    description=issue_data['description'],
                    category=issue_data['category'],
                    priority=issue_data['priority'],
                    location_in_house=issue_data['location_in_house'],
                    status=status,
                    reported_by=user,
                    created_at=timezone.now() - timedelta(days=random.randint(0, 14)),
                )
                
                # Mark resolved if status is resolved or closed
                if status in ['resolved', 'closed']:
                    issue.resolved_at = timezone.now() - timedelta(days=random.randint(0, 7))
                    issue.resolved_by = user
                    issue.resolution_notes = "Issue has been addressed and resolved."
                    issue.save()
                
                # Add 0-2 comments
                num_comments = random.randint(0, 2)
                for _ in range(num_comments):
                    IssueComment.objects.create(
                        issue=issue,
                        user=user,
                        content=random.choice(sample_comments),
                    )
                
                issues_created += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {issues_created} issues'))

