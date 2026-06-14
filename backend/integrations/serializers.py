from rest_framework import serializers

from .models import AutomationWorkflow


class AutomationWorkflowListSerializer(serializers.ModelSerializer):
    farm_id = serializers.SerializerMethodField()
    farm_name = serializers.SerializerMethodField()

    class Meta:
        model = AutomationWorkflow
        fields = [
            'id',
            'slug',
            'name',
            'description',
            'organization',
            'farm_id',
            'farm_name',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_farm_id(self, obj):
        return obj.farm_id

    def get_farm_name(self, obj):
        return obj.farm.name if obj.farm_id else None


class AutomationWorkflowAdminSerializer(serializers.ModelSerializer):
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    webhook_secret = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = AutomationWorkflow
        fields = [
            'id',
            'slug',
            'name',
            'description',
            'webhook_url',
            'webhook_secret',
            'organization',
            'farm',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        organization = attrs.get('organization') or getattr(self.instance, 'organization', None)
        farm = attrs.get('farm', serializers.empty)
        if farm is serializers.empty and self.instance:
            farm = self.instance.farm
        elif farm is serializers.empty:
            farm = None

        if farm and organization and farm.organization_id != organization.id:
            raise serializers.ValidationError(
                {'farm': 'Farm must belong to the same organization as the workflow.'}
            )

        if self.instance is None and not attrs.get('webhook_url'):
            raise serializers.ValidationError({'webhook_url': 'This field is required.'})

        return attrs


class AutomationTriggerSerializer(serializers.Serializer):
    farm_id = serializers.IntegerField(required=False, allow_null=True)
    organization_id = serializers.UUIDField(required=False)
    payload = serializers.DictField(required=False, default=dict)
