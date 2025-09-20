from rest_framework import serializers
from .models import Task, RecurringTask
from houses.serializers import HouseListSerializer


class TaskSerializer(serializers.ModelSerializer):
    house = HouseListSerializer(read_only=True)
    house_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'house', 'house_id', 'day_offset', 'task_name',
            'description', 'task_type', 'is_completed', 'completed_at',
            'completed_by', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskListSerializer(serializers.ModelSerializer):
    house_name = serializers.CharField(source='house.__str__', read_only=True)
    farm_name = serializers.CharField(source='house.farm.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'house_name', 'farm_name', 'day_offset', 'task_name',
            'description', 'task_type', 'is_completed', 'completed_at',
            'completed_by'
        ]


class TaskCompletionSerializer(serializers.Serializer):
    completed_by = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class RecurringTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTask
        fields = [
            'id', 'name', 'description', 'frequency', 'day_of_week',
            'time', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
