from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json


@csrf_exempt
def login_view(request):
    """Simple login with fixed admin credentials"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Check against fixed admin credentials
    if (username == settings.ADMIN_USERNAME and 
        password == settings.ADMIN_PASSWORD):
        
        # Get or create admin user
        user, created = User.objects.get_or_create(
            username=settings.ADMIN_USERNAME,
            defaults={
                'email': settings.ADMIN_EMAIL,
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            user.set_password(settings.ADMIN_PASSWORD)
            user.save()
        
        # Create or get token for API authentication
        token, created = Token.objects.get_or_create(user=user)
        
        # Also login for session-based auth (for admin panel)
        login(request, user)
        
        return JsonResponse({
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff
            }
        })
    
    return JsonResponse({
        'error': 'Invalid credentials'
    }, status=401)


@api_view(['POST'])
def logout_view(request):
    """Logout user"""
    logout(request)
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
def user_info(request):
    """Get current user information"""
    if request.user.is_authenticated:
        return Response({
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'is_staff': request.user.is_staff,
                'is_authenticated': True
            }
        })
    
    return Response({
        'user': {
            'is_authenticated': False
        }
    })


@api_view(['GET'])
def check_auth(request):
    """Check if user is authenticated"""
    return Response({
        'authenticated': request.user.is_authenticated
    })
