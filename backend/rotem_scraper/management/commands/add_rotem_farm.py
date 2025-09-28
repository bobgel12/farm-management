from django.core.management.base import BaseCommand
from rotem_scraper.models import RotemFarm
from django.utils import timezone


class Command(BaseCommand):
    help = 'Add a new farm with Rotem credentials'

    def add_arguments(self, parser):
        parser.add_argument('--farm-name', type=str, required=True, help='Farm name')
        parser.add_argument('--gateway-name', type=str, required=True, help='Gateway name (farm ID)')
        parser.add_argument('--username', type=str, required=True, help='Rotem username')
        parser.add_argument('--password', type=str, required=True, help='Rotem password')
        parser.add_argument('--gateway-alias', type=str, help='Gateway alias (defaults to farm name)')

    def handle(self, *args, **options):
        farm_name = options['farm_name']
        gateway_name = options['gateway_name']
        username = options['username']
        password = options['password']
        gateway_alias = options.get('gateway_alias', farm_name)

        # Check if farm already exists
        if RotemFarm.objects.filter(farm_id=gateway_name).exists():
            self.stdout.write(
                self.style.ERROR(f'Farm with gateway name "{gateway_name}" already exists')
            )
            return

        # Create farm
        farm = RotemFarm.objects.create(
            farm_id=gateway_name,
            farm_name=farm_name,
            gateway_name=gateway_name,
            gateway_alias=gateway_alias,
            rotem_username=username,
            rotem_password=password,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created farm: {farm.farm_name} (ID: {farm.farm_id})')
        )
        self.stdout.write(f'Gateway: {farm.gateway_name}')
        self.stdout.write(f'Username: {farm.rotem_username}')
        self.stdout.write(f'Password: {"*" * len(farm.rotem_password)}')
