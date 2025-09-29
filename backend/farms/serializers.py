from rest_framework import serializers
from .models import Farm, Worker, Program, ProgramTask


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
            'id', 'name', 'location', 'description', 'contact_person',
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
            'id', 'name', 'location', 'description', 'is_active',
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
            'id', 'name', 'location', 'contact_person',
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
