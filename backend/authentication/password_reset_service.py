"""
Password reset service for secure password reset functionality
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.db import transaction
from .models import PasswordResetToken, SecurityEvent, LoginAttempt
from django.contrib.auth.models import User
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for handling password reset operations"""
    
    @staticmethod
    def request_password_reset(email, ip_address=None, user_agent=None):
        """Request a password reset for the given email"""
        try:
            # Find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Don't reveal if email exists or not for security
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return {
                    'success': True,
                    'message': 'If an account with this email exists, you will receive a password reset link.'
                }
            
            # Invalidate any existing unused tokens for this user
            PasswordResetToken.objects.filter(
                user=user, 
                used=False
            ).update(used=True)
            
            # Create new token (expires in 1 hour)
            token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timezone.timedelta(hours=1),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Send password reset email
            success = PasswordResetService._send_password_reset_email(user, token)
            
            if success:
                # Log security event
                SecurityEvent.objects.create(
                    user=user,
                    event_type='password_reset_requested',
                    description=f'Password reset requested for {user.username}',
                    ip_address=ip_address or 'Unknown',
                    user_agent=user_agent or 'Unknown'
                )
                
                return {
                    'success': True,
                    'message': 'If an account with this email exists, you will receive a password reset link.'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send password reset email. Please try again later.'
                }
                
        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred. Please try again later.'
            }
    
    @staticmethod
    def _send_password_reset_email(user, token):
        """Send password reset email to user"""
        try:
            # Create reset URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
            
            # Email content
            subject = 'Password Reset Request - Chicken House Management'
            
            # Text content
            text_content = f"""
Hello {user.first_name or user.username},

You have requested to reset your password for the Chicken House Management System.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
Chicken House Management Team
            """
            
            # HTML content
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Password Reset</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c5aa0; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐔 Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello {user.first_name or user.username},</p>
            <p>You have requested to reset your password for the Chicken House Management System.</p>
            <p>Click the button below to reset your password:</p>
            <a href="{reset_url}" class="button">Reset Password</a>
            <p><strong>This link will expire in 1 hour</strong> for security reasons.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>Chicken House Management Team</p>
        </div>
    </div>
</body>
</html>
            """
            
            # Send email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False
    
    @staticmethod
    def reset_password(token_value, new_password, ip_address=None, user_agent=None):
        """Reset password using token"""
        try:
            # Find and validate token
            try:
                token = PasswordResetToken.objects.get(token=token_value)
            except PasswordResetToken.DoesNotExist:
                return {
                    'success': False,
                    'message': 'Invalid or expired reset token.'
                }
            
            if not token.is_valid():
                return {
                    'success': False,
                    'message': 'Invalid or expired reset token.'
                }
            
            # Validate password strength
            password_validation = PasswordResetService._validate_password_strength(new_password)
            if not password_validation['valid']:
                return {
                    'success': False,
                    'message': password_validation['message']
                }
            
            # Reset password
            with transaction.atomic():
                user = token.user
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                token.mark_as_used()
                
                # Invalidate all other reset tokens for this user
                PasswordResetToken.objects.filter(
                    user=user,
                    used=False
                ).update(used=True)
                
                # Log security event
                SecurityEvent.objects.create(
                    user=user,
                    event_type='password_reset_completed',
                    description=f'Password reset completed for {user.username}',
                    ip_address=ip_address or 'Unknown',
                    user_agent=user_agent or 'Unknown'
                )
            
            logger.info(f"Password reset completed for user {user.username}")
            return {
                'success': True,
                'message': 'Password has been reset successfully. You can now log in with your new password.'
            }
            
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while resetting your password. Please try again.'
            }
    
    @staticmethod
    def _validate_password_strength(password):
        """Validate password strength"""
        if len(password) < 8:
            return {
                'valid': False,
                'message': 'Password must be at least 8 characters long.'
            }
        
        if len(password) > 128:
            return {
                'valid': False,
                'message': 'Password must be no more than 128 characters long.'
            }
        
        # Check for common patterns
        if password.lower() in ['password', '12345678', 'qwerty123', 'admin123']:
            return {
                'valid': False,
                'message': 'Password is too common. Please choose a more secure password.'
            }
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not has_letter or not has_number:
            return {
                'valid': False,
                'message': 'Password must contain at least one letter and one number.'
            }
        
        return {'valid': True, 'message': 'Password is valid.'}
    
    @staticmethod
    def log_login_attempt(username, ip_address, success, failure_reason=None, user_agent=None):
        """Log login attempt for security monitoring"""
        try:
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent or 'Unknown',
                success=success,
                failure_reason=failure_reason or ''
            )
        except Exception as e:
            logger.error(f"Failed to log login attempt: {str(e)}")
    
    @staticmethod
    def check_rate_limit(ip_address, username=None):
        """Check if IP or username is rate limited"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Check IP-based rate limiting (max 10 failed attempts per hour)
        recent_failures = LoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False,
            attempted_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failures >= 10:
            return {
                'limited': True,
                'message': 'Too many failed login attempts. Please try again later.'
            }
        
        # Check username-based rate limiting (max 5 failed attempts per hour)
        if username:
            recent_failures = LoginAttempt.objects.filter(
                username=username,
                success=False,
                attempted_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            if recent_failures >= 5:
                return {
                    'limited': True,
                    'message': 'Too many failed login attempts for this username. Please try again later.'
                }
        
        return {'limited': False, 'message': 'OK'}
