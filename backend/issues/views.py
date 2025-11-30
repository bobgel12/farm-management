from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Issue, IssuePhoto, IssueComment
from .serializers import (
    IssueListSerializer, IssueDetailSerializer, IssueCreateSerializer,
    IssueUpdateSerializer, IssueResolveSerializer, CreateTaskFromIssueSerializer,
    IssuePhotoSerializer, IssuePhotoCreateSerializer, IssueCommentSerializer
)
from .services.cloudinary_service import upload_photo, delete_photo


class IssueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing issues.
    
    Endpoints:
    - GET /api/issues/ - List all issues (filterable by house, status, category)
    - POST /api/issues/ - Create a new issue with optional photos
    - GET /api/issues/{id}/ - Get issue details
    - PUT/PATCH /api/issues/{id}/ - Update issue
    - DELETE /api/issues/{id}/ - Delete issue
    - POST /api/issues/{id}/photos/ - Add photos to issue
    - POST /api/issues/{id}/resolve/ - Resolve issue
    - POST /api/issues/{id}/reopen/ - Reopen issue
    - POST /api/issues/{id}/create-task/ - Create task from issue
    - POST /api/issues/{id}/comments/ - Add comment to issue
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Issue.objects.select_related(
            'house', 'house__farm', 'reported_by', 'assigned_to', 'resolved_by'
        ).prefetch_related('photos', 'comments')
        
        # Filter by house
        house_id = self.request.query_params.get('house_id')
        if house_id:
            queryset = queryset.filter(house_id=house_id)
        
        # Filter by farm
        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            queryset = queryset.filter(house__farm_id=farm_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            if status_filter == 'open':
                queryset = queryset.filter(status__in=['open', 'in_progress'])
            else:
                queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by assigned to current user
        my_issues = self.request.query_params.get('my_issues')
        if my_issues == 'true':
            queryset = queryset.filter(
                Q(reported_by=self.request.user) | Q(assigned_to=self.request.user)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return IssueListSerializer
        elif self.action == 'create':
            return IssueCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return IssueUpdateSerializer
        elif self.action == 'resolve':
            return IssueResolveSerializer
        elif self.action == 'create_task':
            return CreateTaskFromIssueSerializer
        return IssueDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def photos(self, request, pk=None):
        """Add photos to an existing issue"""
        issue = self.get_object()
        
        photos_data = request.data.get('photos', [])
        if not photos_data:
            # Check for single photo upload
            image = request.data.get('image')
            caption = request.data.get('caption', '')
            if image:
                photos_data = [{'image': image, 'caption': caption}]
        
        if not photos_data:
            return Response(
                {'error': 'No photos provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_photos = []
        for photo_data in photos_data:
            upload_result = upload_photo(photo_data.get('image'))
            if upload_result:
                photo = IssuePhoto.objects.create(
                    issue=issue,
                    cloudinary_url=upload_result['url'],
                    cloudinary_public_id=upload_result['public_id'],
                    caption=photo_data.get('caption', ''),
                    uploaded_by=request.user
                )
                created_photos.append(IssuePhotoSerializer(photo).data)
        
        return Response({'photos': created_photos}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='photos/(?P<photo_id>[^/.]+)')
    def delete_photo(self, request, pk=None, photo_id=None):
        """Delete a photo from an issue"""
        issue = self.get_object()
        photo = get_object_or_404(IssuePhoto, id=photo_id, issue=issue)
        
        # Delete from Cloudinary
        delete_photo(photo.cloudinary_public_id)
        
        # Delete from database
        photo.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark issue as resolved"""
        issue = self.get_object()
        serializer = IssueResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        issue.resolve(
            resolved_by=request.user,
            resolution_notes=serializer.validated_data.get('resolution_notes', '')
        )
        
        return Response(IssueDetailSerializer(issue).data)
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen a resolved/closed issue"""
        issue = self.get_object()
        issue.reopen()
        
        return Response(IssueDetailSerializer(issue).data)
    
    @action(detail=True, methods=['post'], url_path='create-task')
    def create_task(self, request, pk=None):
        """Create a task from this issue"""
        from tasks.models import Task
        from workers.models import Worker
        
        issue = self.get_object()
        serializer = CreateTaskFromIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create task
        if issue.created_task:
            return Response(
                {'error': 'Task already created from this issue'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare task data
        title = serializer.validated_data.get('title', f"[Issue] {issue.title}")
        worker_id = serializer.validated_data.get('worker_id')
        due_date = serializer.validated_data.get('due_date', timezone.now().date())
        priority = serializer.validated_data.get('priority', 'medium')
        
        # Map issue priority to task priority
        priority_map = {
            'low': 'low',
            'medium': 'normal',
            'high': 'high',
            'critical': 'high'
        }
        
        # Build task description with issue details
        description = (
            f"Issue Category: {issue.get_category_display()}\n"
            f"Priority: {issue.get_priority_display()}\n"
            f"Location: {issue.location_in_house or 'Not specified'}\n\n"
            f"Description:\n{issue.description}"
        )
        
        # Create task
        task_data = {
            'title': title,
            'description': description,
            'task_type': 'general',  # or map from category
            'day': issue.house.age_days or 0,
            'house': issue.house,
            'priority': priority_map.get(issue.priority, 'normal'),
            'due_date': due_date,
            'status': 'pending'
        }
        
        # Assign worker if provided
        if worker_id:
            try:
                worker = Worker.objects.get(id=worker_id)
                task_data['assigned_to'] = worker
            except Worker.DoesNotExist:
                pass
        
        task = Task.objects.create(**task_data)
        
        # Link task to issue
        issue.created_task = task
        issue.status = 'in_progress'
        issue.save()
        
        return Response({
            'task_id': task.id,
            'task_title': task.title,
            'message': 'Task created successfully'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post', 'get'])
    def comments(self, request, pk=None):
        """Add or list comments on an issue"""
        issue = self.get_object()
        
        if request.method == 'GET':
            comments = issue.comments.select_related('user').all()
            serializer = IssueCommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        # POST - add comment
        serializer = IssueCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comment = IssueComment.objects.create(
            issue=issue,
            user=request.user,
            content=serializer.validated_data['content']
        )
        
        return Response(
            IssueCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )

