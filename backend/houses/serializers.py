from rest_framework import serializers
from .models import House
from farms.serializers import FarmListSerializer


class HouseSerializer(serializers.ModelSerializer):
    farm = FarmListSerializer(read_only=True)
    farm_id = serializers.IntegerField(write_only=True)
    current_day = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = House
        fields = [
            'id', 'farm', 'farm_id', 'house_number', 'chicken_in_date',
            'chicken_out_date', 'chicken_out_day', 'is_active',
            'current_day', 'days_remaining', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate that chicken_out_day is positive
        if data.get('chicken_out_day', 40) <= 0:
            raise serializers.ValidationError("Chicken out day must be positive")
        
        # Validate that chicken_in_date is not in the future
        if data.get('chicken_in_date'):
            from django.utils import timezone
            if data['chicken_in_date'] > timezone.now().date():
                raise serializers.ValidationError("Chicken in date cannot be in the future")
        
        return data


class HouseListSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    current_day = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = House
        fields = [
            'id', 'farm_name', 'house_number', 'chicken_in_date',
            'chicken_out_date', 'current_day', 'days_remaining',
            'status', 'is_active'
        ]
