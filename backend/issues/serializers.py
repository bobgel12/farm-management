from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Issue, IssuePhoto, IssueComment


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for display"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class IssuePhotoSerializer(serializers.ModelSerializer):
    """Serializer for issue photos"""
    uploaded_by = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = IssuePhoto
        fields = ['id', 'cloudinary_url', 'cloudinary_public_id', 'caption', 
                  'uploaded_at', 'uploaded_by']
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']


class IssuePhotoCreateSerializer(serializers.Serializer):
    """Serializer for creating photos with base64/file upload"""
    image = serializers.CharField(help_text="Base64 encoded image or URL")
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True)


class IssueCommentSerializer(serializers.ModelSerializer):
    """Serializer for issue comments"""
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = IssueComment
        fields = ['id', 'content', 'user', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class IssueListSerializer(serializers.ModelSerializer):
    """Serializer for listing issues (minimal info)"""
    reported_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    house_number = serializers.IntegerField(source='house.house_number', read_only=True)
    farm_name = serializers.CharField(source='house.farm.name', read_only=True)
    photo_count = serializers.ReadOnlyField()
    age_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Issue
        fields = [
            'id', 'title', 'category', 'priority', 'status',
            'house', 'house_number', 'farm_name',
            'reported_by', 'assigned_to',
            'photo_count', 'age_display',
            'created_at', 'updated_at'
        ]


class IssueDetailSerializer(serializers.ModelSerializer):
    """Serializer for full issue details"""
    reported_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    resolved_by = UserMinimalSerializer(read_only=True)
    house_number = serializers.IntegerField(source='house.house_number', read_only=True)
    farm_name = serializers.CharField(source='house.farm.name', read_only=True)
    photos = IssuePhotoSerializer(many=True, read_only=True)
    comments = IssueCommentSerializer(many=True, read_only=True)
    photo_count = serializers.ReadOnlyField()
    age_display = serializers.ReadOnlyField()
    is_open = serializers.ReadOnlyField()
    
    class Meta:
        model = Issue
        fields = [
            'id', 'title', 'description', 'category', 'priority', 'status',
            'location_in_house',
            'house', 'house_number', 'farm_name',
            'reported_by', 'assigned_to', 'resolved_by',
            'created_task',
            'photos', 'comments',
            'photo_count', 'age_display', 'is_open',
            'resolution_notes', 'resolved_at',
            'created_at', 'updated_at'
        ]


class IssueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating issues with optional photos"""
    photos = IssuePhotoCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Issue
        fields = [
            'house', 'title', 'description', 'category', 'priority',
            'location_in_house', 'photos'
        ]
    
    def create(self, validated_data):
        photos_data = validated_data.pop('photos', [])
        issue = Issue.objects.create(**validated_data)
        
        # Handle photo uploads
        if photos_data:
            from .services.cloudinary_service import upload_photo
            
            for photo_data in photos_data:
                upload_result = upload_photo(photo_data.get('image'))
                if upload_result:
                    IssuePhoto.objects.create(
                        issue=issue,
                        cloudinary_url=upload_result['url'],
                        cloudinary_public_id=upload_result['public_id'],
                        caption=photo_data.get('caption', ''),
                        uploaded_by=self.context['request'].user
                    )
        
        return issue


class IssueUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating issues"""
    
    class Meta:
        model = Issue
        fields = [
            'title', 'description', 'category', 'priority', 'status',
            'location_in_house', 'assigned_to'
        ]


class IssueResolveSerializer(serializers.Serializer):
    """Serializer for resolving issues"""
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class CreateTaskFromIssueSerializer(serializers.Serializer):
    """Serializer for creating a task from an issue"""
    title = serializers.CharField(max_length=200, required=False)
    worker_id = serializers.IntegerField(required=False)
    due_date = serializers.DateField(required=False)
    priority = serializers.ChoiceField(
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )

