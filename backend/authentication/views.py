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
    
    # Authenticate user using Django's authentication system
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        try:
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
        logger.info(f"Password change request from user: {request.user.username}")
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        logger.info(f"Password change data received - current_password: {'*' * len(current_password) if current_password else 'None'}, new_password: {'*' * len(new_password) if new_password else 'None'}")
        
        if not current_password or not new_password:
            logger.warning("Password change failed: Missing current_password or new_password")
            return Response({'error': 'Current password and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify current password
        if not request.user.check_password(current_password):
            logger.warning(f"Password change failed: Incorrect current password for user {request.user.username}")
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Current password verified for user {request.user.username}")
        
        # Validate new password strength
        password_validation = PasswordResetService._validate_password_strength(new_password)
        if not password_validation['valid']:
            logger.warning(f"Password change failed: Password validation failed for user {request.user.username} - {password_validation['message']}")
            return Response({'error': password_validation['message']}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Password validation passed for user {request.user.username}")
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        logger.info(f"Password successfully changed for user {request.user.username}")
        
        # Log security event
        ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Ensure IP address is valid for the model
        if not ip_address or ip_address == 'Unknown':
            ip_address = '127.0.0.1'
        
        try:
            SecurityEvent.objects.create(
                user=request.user,
                event_type='password_changed',
                description=f'Password changed for {request.user.username}',
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.warning(f"Failed to log security event: {str(e)}")
            # Don't fail the password change if logging fails
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
