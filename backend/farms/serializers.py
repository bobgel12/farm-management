from rest_framework import serializers
from django.db.models import Sum
from .models import Farm, Worker, Program, ProgramTask, Breed, Flock, FlockPerformance, FlockComparison, MortalityRecord


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = [
            'id', 'name', 'email', 'phone', 'role',
            'is_active', 'receive_daily_tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FarmSerializer(serializers.ModelSerializer):
    total_houses = serializers.ReadOnlyField()
    active_houses = serializers.ReadOnlyField()
    workers = WorkerSerializer(many=True, read_only=True)
    houses = serializers.SerializerMethodField()
    is_integrated = serializers.ReadOnlyField()
    integration_display_name = serializers.ReadOnlyField()

    class Meta:
        model = Farm
        fields = [
            'id', 'organization', 'name', 'location', 'description', 'contact_person',
            'contact_phone', 'contact_email', 'is_active',
            'total_houses', 'active_houses', 'workers', 'houses',
            'has_system_integration', 'integration_type', 'integration_status',
            'last_sync', 'is_integrated', 'integration_display_name',
            'rotem_farm_id', 'rotem_username', 'rotem_password',
            'rotem_gateway_name', 'rotem_gateway_alias',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'rotem_password': {'write_only': True}
        }

    def get_houses(self, obj):
        """Get houses for this farm"""
        from houses.models import House
        houses = House.objects.filter(farm=obj)
        return [
            {
                'id': house.id,
                'house_number': house.house_number,
                'capacity': house.capacity,
                'is_integrated': house.is_integrated,
                'current_age_days': house.current_age_days,
                'batch_start_date': house.batch_start_date,
                'expected_harvest_date': house.expected_harvest_date,
                'is_active': house.is_active,
                'last_system_sync': house.last_system_sync,
                'created_at': house.created_at,
                'updated_at': house.updated_at
            }
            for house in houses
        ]


class FarmListSerializer(serializers.ModelSerializer):
    total_houses = serializers.ReadOnlyField()
    active_houses = serializers.ReadOnlyField()
    is_integrated = serializers.ReadOnlyField()
    integration_display_name = serializers.ReadOnlyField()

    class Meta:
        model = Farm
        fields = [
            'id', 'organization', 'name', 'location', 'description', 'is_active',
            'total_houses', 'active_houses', 'has_system_integration',
            'integration_type', 'integration_status', 'last_sync',
            'is_integrated', 'integration_display_name'
        ]


class ProgramTaskSerializer(serializers.ModelSerializer):
    is_recurring = serializers.ReadOnlyField()
    is_setup_task = serializers.ReadOnlyField()

    class Meta:
        model = ProgramTask
        fields = [
            'id', 'day', 'task_type', 'title', 'description', 'instructions',
            'priority', 'estimated_duration', 'is_required', 'requires_confirmation',
            'recurring_days', 'is_recurring', 'is_setup_task', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_recurring_days(self, value):
        """Validate recurring days are valid weekday numbers (0-6)"""
        if value:
            for day in value:
                if not isinstance(day, int) or day < 0 or day > 6:
                    raise serializers.ValidationError(
                        "Recurring days must be integers between 0 (Monday) and 6 (Sunday)"
                    )
        return value

    def validate(self, data):
        """Validate that recurring tasks have recurring_days set"""
        if data.get('task_type') == 'recurring' and not data.get('recurring_days'):
            raise serializers.ValidationError(
                "Recurring tasks must specify recurring_days"
            )
        return data


class ProgramSerializer(serializers.ModelSerializer):
    total_tasks = serializers.ReadOnlyField()
    tasks = ProgramTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Program
        fields = [
            'id', 'name', 'description', 'duration_days', 'is_active',
            'is_default', 'total_tasks', 'tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_is_default(self, value):
        """Ensure only one default program exists"""
        if value and Program.objects.filter(is_default=True).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(
                "Only one program can be set as default"
            )
        return value


class ProgramListSerializer(serializers.ModelSerializer):
    total_tasks = serializers.ReadOnlyField()

    class Meta:
        model = Program
        fields = [
            'id', 'name', 'description', 'duration_days', 'is_active',
            'is_default', 'total_tasks', 'created_at', 'updated_at'
        ]


class FarmWithProgramSerializer(serializers.ModelSerializer):
    total_houses = serializers.ReadOnlyField()
    active_houses = serializers.ReadOnlyField()
    workers = WorkerSerializer(many=True, read_only=True)
    program = ProgramListSerializer(read_only=True)
    program_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Farm
        fields = [
            'id', 'organization', 'name', 'location', 'contact_person',
            'contact_phone', 'contact_email', 'program', 'program_id',
            'is_active', 'total_houses', 'active_houses', 'workers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        program_id = validated_data.pop('program_id', None)
        if program_id:
            validated_data['program_id'] = program_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        program_id = validated_data.pop('program_id', None)
        if program_id:
            validated_data['program_id'] = program_id
        return super().update(instance, validated_data)


class BreedSerializer(serializers.ModelSerializer):
    """Serializer for Breed model"""
    class Meta:
        model = Breed
        fields = [
            'id', 'name', 'code', 'description',
            'average_weight_gain_per_week', 'average_feed_conversion_ratio',
            'average_mortality_rate', 'typical_harvest_age_days',
            'typical_harvest_weight_grams', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BreedListSerializer(serializers.ModelSerializer):
    """Simplified serializer for breed list"""
    class Meta:
        model = Breed
        fields = ['id', 'name', 'code', 'typical_harvest_age_days', 'is_active']


class FlockPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for FlockPerformance model"""
    flock_code = serializers.CharField(source='flock.flock_code', read_only=True)
    batch_number = serializers.CharField(source='flock.batch_number', read_only=True)
    
    class Meta:
        model = FlockPerformance
        fields = [
            'id', 'flock', 'flock_code', 'batch_number',
            'record_date', 'flock_age_days',
            'average_weight_grams', 'total_weight_kg',
            'feed_consumed_kg', 'daily_feed_consumption_kg', 'feed_conversion_ratio',
            'daily_water_consumption_liters',
            'current_chicken_count', 'mortality_count',
            'mortality_rate', 'livability',
            'average_temperature', 'average_humidity',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FlockSerializer(serializers.ModelSerializer):
    """Serializer for Flock model"""
    breed = BreedListSerializer(read_only=True)
    breed_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    house_name = serializers.CharField(source='house.__str__', read_only=True)
    farm_name = serializers.CharField(source='house.farm.name', read_only=True)
    current_age_days = serializers.ReadOnlyField()
    days_until_harvest = serializers.ReadOnlyField()
    mortality_count = serializers.ReadOnlyField()
    mortality_rate = serializers.ReadOnlyField()
    livability = serializers.ReadOnlyField()
    performance_records = FlockPerformanceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Flock
        fields = [
            'id', 'house', 'house_name', 'farm_name',
            'breed', 'breed_id',
            'batch_number', 'flock_code',
            'arrival_date', 'expected_harvest_date', 'actual_harvest_date',
            'start_date', 'end_date',
            'initial_chicken_count', 'current_chicken_count',
            'status', 'is_active',
            'supplier', 'notes',
            'current_age_days', 'days_until_harvest',
            'mortality_count', 'mortality_rate', 'livability',
            'performance_records',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'flock_code', 'created_at', 'updated_at', 'created_by']
    
    def create(self, validated_data):
        """Create flock and set created_by"""
        breed_id = validated_data.pop('breed_id', None)
        if breed_id:
            validated_data['breed_id'] = breed_id
        
        # Auto-generate flock_code if not provided
        if 'flock_code' not in validated_data or not validated_data.get('flock_code'):
            house = validated_data.get('house')
            batch_number = validated_data.get('batch_number', '')
            arrival_date = validated_data.get('arrival_date')
            
            # Generate flock_code: HOUSE-BATCH-YYYYMMDD
            house_str = str(house.id) if house else 'UNK'
            date_str = arrival_date.strftime('%Y%m%d') if arrival_date else ''
            validated_data['flock_code'] = f"{house_str}-{batch_number}-{date_str}"
        
        # Set created_by from request user if available
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class FlockListSerializer(serializers.ModelSerializer):
    """Simplified serializer for flock list"""
    breed_name = serializers.CharField(source='breed.name', read_only=True)
    house_name = serializers.CharField(source='house.__str__', read_only=True)
    current_age_days = serializers.ReadOnlyField()
    days_until_harvest = serializers.ReadOnlyField()
    mortality_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Flock
        fields = [
            'id', 'house', 'house_name', 'breed_name',
            'batch_number', 'flock_code',
            'arrival_date', 'expected_harvest_date', 'actual_harvest_date',
            'status', 'is_active',
            'initial_chicken_count', 'current_chicken_count',
            'current_age_days', 'days_until_harvest', 'mortality_rate'
        ]


class FlockComparisonSerializer(serializers.ModelSerializer):
    """Serializer for FlockComparison model"""
    flocks = FlockListSerializer(many=True, read_only=True)
    flock_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    creator_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FlockComparison
        fields = [
            'id', 'name', 'description',
            'flocks', 'flock_ids',
            'comparison_metrics', 'comparison_results',
            'created_by', 'creator_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create comparison and add flocks"""
        flock_ids = validated_data.pop('flock_ids', [])
        
        # Set created_by from request user
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        comparison = super().create(validated_data)
        
        # Add flocks
        if flock_ids:
            comparison.flocks.set(flock_ids)
        
        return comparison
    
    def update(self, instance, validated_data):
        """Update comparison and flocks"""
        flock_ids = validated_data.pop('flock_ids', None)
        
        comparison = super().update(instance, validated_data)
        
        # Update flocks if provided
        if flock_ids is not None:
            comparison.flocks.set(flock_ids)
        
        return comparison


# Mortality Recording Serializers

class MortalityRecordSerializer(serializers.ModelSerializer):
    """Serializer for MortalityRecord model"""
    flock_code = serializers.CharField(source='flock.flock_code', read_only=True)
    house_number = serializers.IntegerField(source='house.house_number', read_only=True)
    farm_name = serializers.CharField(source='house.farm.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    has_detailed_breakdown = serializers.ReadOnlyField()
    breakdown_total = serializers.ReadOnlyField()
    
    class Meta:
        model = MortalityRecord
        fields = [
            'id', 'flock', 'flock_code', 'house', 'house_number', 'farm_name',
            'record_date', 'total_deaths',
            'disease_deaths', 'culling_deaths', 'accident_deaths',
            'heat_stress_deaths', 'cold_stress_deaths', 'unknown_deaths', 'other_deaths',
            'notes', 'recorded_by', 'recorded_by_name',
            'has_detailed_breakdown', 'breakdown_total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate that breakdown doesn't exceed total"""
        total = data.get('total_deaths', 0)
        breakdown = (
            data.get('disease_deaths', 0) +
            data.get('culling_deaths', 0) +
            data.get('accident_deaths', 0) +
            data.get('heat_stress_deaths', 0) +
            data.get('cold_stress_deaths', 0) +
            data.get('unknown_deaths', 0) +
            data.get('other_deaths', 0)
        )
        
        if breakdown > 0 and breakdown > total:
            raise serializers.ValidationError(
                "Sum of detailed breakdown cannot exceed total deaths"
            )
        
        return data


class MortalityRecordCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating mortality records"""
    
    class Meta:
        model = MortalityRecord
        fields = [
            'flock', 'house', 'record_date', 'total_deaths',
            'disease_deaths', 'culling_deaths', 'accident_deaths',
            'heat_stress_deaths', 'cold_stress_deaths', 'unknown_deaths', 'other_deaths',
            'notes'
        ]
    
    def validate(self, data):
        """Validate data and check for duplicate records"""
        # Check for existing record on same date
        flock = data.get('flock')
        record_date = data.get('record_date')
        
        if MortalityRecord.objects.filter(flock=flock, record_date=record_date).exists():
            raise serializers.ValidationError(
                "A mortality record already exists for this flock on this date"
            )
        
        return data
    
    def create(self, validated_data):
        """Create mortality record and set recorded_by"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['recorded_by'] = request.user
        return super().create(validated_data)


class MortalitySummarySerializer(serializers.Serializer):
    """Serializer for mortality summary data"""
    flock_id = serializers.IntegerField()
    flock_code = serializers.CharField()
    house_number = serializers.IntegerField()
    initial_count = serializers.IntegerField()
    current_count = serializers.IntegerField()
    total_mortality = serializers.IntegerField()
    mortality_rate = serializers.FloatField()
    livability = serializers.FloatField()
    records_count = serializers.IntegerField()
    
    # Breakdown by cause
    disease_total = serializers.IntegerField()
    culling_total = serializers.IntegerField()
    accident_total = serializers.IntegerField()
    heat_stress_total = serializers.IntegerField()
    cold_stress_total = serializers.IntegerField()
    unknown_total = serializers.IntegerField()
    other_total = serializers.IntegerField()
    
    # Recent trends
    last_7_days = serializers.IntegerField()
    last_30_days = serializers.IntegerField()
    daily_average = serializers.FloatField()
