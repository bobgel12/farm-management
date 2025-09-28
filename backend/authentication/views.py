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
from django.utils import timezone
from django.db import transaction
from .models import PasswordResetToken, SecurityEvent, LoginAttempt
from .password_reset_service import PasswordResetService
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def login_view(request):
    """Secure login with rate limiting and security monitoring"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Get client information
    ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except json.JSONDecodeError:
        # Log failed attempt
        PasswordResetService.log_login_attempt(
            username='Unknown', 
            ip_address=ip_address, 
            success=False, 
            failure_reason='Invalid JSON',
            user_agent=user_agent
        )
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Check rate limiting
    rate_limit_check = PasswordResetService.check_rate_limit(ip_address, username)
    if rate_limit_check['limited']:
        return JsonResponse({'error': rate_limit_check['message']}, status=429)
    
    # Check against fixed admin credentials
    if (username == settings.ADMIN_USERNAME and 
        password == settings.ADMIN_PASSWORD):
        
        try:
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
            
            # Log successful login
            PasswordResetService.log_login_attempt(
                username=username,
                ip_address=ip_address,
                success=True,
                user_agent=user_agent
            )
            
            # Log security event
            SecurityEvent.objects.create(
                user=user,
                event_type='login_from_new_device',
                description=f'Successful login from {ip_address}',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
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
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            # Log failed attempt
            PasswordResetService.log_login_attempt(
                username=username,
                ip_address=ip_address,
                success=False,
                failure_reason='System error',
                user_agent=user_agent
            )
            return JsonResponse({'error': 'Login failed'}, status=500)
    
    # Log failed attempt
    PasswordResetService.log_login_attempt(
        username=username,
        ip_address=ip_address,
        success=False,
        failure_reason='Invalid credentials',
        user_agent=user_agent
    )
    
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


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Request password reset via email"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client information
        ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Request password reset
        result = PasswordResetService.request_password_reset(email, ip_address, user_agent)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using token"""
    try:
        data = json.loads(request.body)
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not token or not new_password:
            return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client information
        ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Reset password
        result = PasswordResetService.reset_password(token, new_password, ip_address, user_agent)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for authenticated user"""
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return Response({'error': 'Current password and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify current password
        if not request.user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password strength
        password_validation = PasswordResetService._validate_password_strength(new_password)
        if not password_validation['valid']:
            return Response({'error': password_validation['message']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        # Log security event
        ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        SecurityEvent.objects.create(
            user=request.user,
            event_type='password_changed',
            description=f'Password changed for {request.user.username}',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
