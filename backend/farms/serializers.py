from rest_framework import serializers
from .models import Farm, Worker


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

    class Meta:
        model = Farm
        fields = [
            'id', 'name', 'location', 'contact_person',
            'contact_phone', 'contact_email', 'is_active',
            'total_houses', 'active_houses', 'workers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FarmListSerializer(serializers.ModelSerializer):
    total_houses = serializers.ReadOnlyField()
    active_houses = serializers.ReadOnlyField()

    class Meta:
        model = Farm
        fields = [
            'id', 'name', 'location', 'is_active',
            'total_houses', 'active_houses'
        ]
