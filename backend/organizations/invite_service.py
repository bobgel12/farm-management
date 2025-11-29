"""
Organization invite service for sending and managing organization invitations
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from .models import Organization, OrganizationUser, OrganizationInvite
import logging
import secrets
from datetime import timedelta

logger = logging.getLogger(__name__)


class OrganizationInviteService:
    """Service for handling organization invitations"""
    
    # Invite expires in 7 days
    INVITE_EXPIRY_DAYS = 7
    
    @staticmethod
    def generate_token():
        """Generate a secure random token for invite"""
        return secrets.token_urlsafe(48)
    
    @staticmethod
    def create_invite(organization, email, invited_by, role='worker', 
                      can_manage_farms=False, can_manage_users=False,
                      can_view_reports=True, can_export_data=False):
        """Create and send an organization invite"""
        try:
            # Check if email is already a member of the organization
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                existing_membership = OrganizationUser.objects.filter(
                    organization=organization,
                    user=existing_user,
                    is_active=True
                ).exists()
                if existing_membership:
                    return {
                        'success': False,
                        'message': 'This user is already a member of the organization.'
                    }
            
            # Check if there's already a pending invite for this email
            existing_invite = OrganizationInvite.objects.filter(
                organization=organization,
                email=email,
                status='pending'
            ).first()
            
            if existing_invite:
                if existing_invite.is_valid:
                    return {
                        'success': False,
                        'message': 'An invite has already been sent to this email address.',
                        'invite': existing_invite
                    }
                else:
                    # Mark old invite as expired and create new one
                    existing_invite.mark_expired()
            
            # Check organization user limit
            if not organization.can_add_user():
                return {
                    'success': False,
                    'message': 'Organization has reached maximum user limit.'
                }
            
            # Create the invite
            invite = OrganizationInvite.objects.create(
                organization=organization,
                email=email,
                token=OrganizationInviteService.generate_token(),
                role=role,
                can_manage_farms=can_manage_farms,
                can_manage_users=can_manage_users,
                can_view_reports=can_view_reports,
                can_export_data=can_export_data,
                invited_by=invited_by,
                expires_at=timezone.now() + timedelta(days=OrganizationInviteService.INVITE_EXPIRY_DAYS)
            )
            
            # Send invite email
            email_sent = OrganizationInviteService._send_invite_email(invite)
            
            if email_sent:
                logger.info(f"Organization invite sent to {email} for {organization.name}")
                return {
                    'success': True,
                    'message': f'Invitation sent to {email}',
                    'invite': invite
                }
            else:
                # Still save the invite even if email failed (can be shared manually)
                logger.warning(f"Email failed but invite created for {email} to {organization.name}")
                return {
                    'success': True,
                    'message': f'Invitation created for {email} (email delivery failed - share the link manually)',
                    'invite': invite,
                    'email_sent': False
                }
                
        except Exception as e:
            logger.error(f"Failed to create organization invite: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while creating the invitation.'
            }
    
    @staticmethod
    def _send_invite_email(invite):
        """Send invitation email"""
        try:
            # Create invite URL
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            invite_url = f"{frontend_url}/accept-invite/{invite.token}"
            
            # Email content
            subject = f"You've been invited to join {invite.organization.name}"
            
            inviter_name = invite.invited_by.get_full_name() or invite.invited_by.username if invite.invited_by else 'A team member'
            
            # Text content
            text_content = f"""
Hello,

{inviter_name} has invited you to join {invite.organization.name} on Chicken House Management System.

You've been assigned the role of: {invite.get_role_display()}

Click the link below to accept the invitation:
{invite_url}

This invitation will expire on {invite.expires_at.strftime('%B %d, %Y at %I:%M %p')}.

If you did not expect this invitation, you can safely ignore this email.

Best regards,
Chicken House Management Team
            """
            
            # HTML content
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Organization Invitation</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c5aa0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; background-color: #2c5aa0; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
        .button:hover {{ background-color: #1e4080; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .role-badge {{ display: inline-block; background-color: #e3f2fd; color: #1565c0; padding: 4px 12px; border-radius: 20px; font-size: 14px; }}
        .info-box {{ background-color: #fff; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #2c5aa0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐔 You're Invited!</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p><strong>{inviter_name}</strong> has invited you to join <strong>{invite.organization.name}</strong> on Chicken House Management System.</p>
            
            <div class="info-box">
                <p style="margin: 0;"><strong>Your Role:</strong> <span class="role-badge">{invite.get_role_display()}</span></p>
            </div>
            
            <p style="text-align: center;">
                <a href="{invite_url}" class="button">Accept Invitation</a>
            </p>
            
            <p style="font-size: 13px; color: #666;">
                This invitation will expire on <strong>{invite.expires_at.strftime('%B %d, %Y at %I:%M %p')}</strong>.
            </p>
            
            <p style="font-size: 13px; color: #666;">
                If you did not expect this invitation, you can safely ignore this email.
            </p>
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
                recipient_list=[invite.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Invite email sent to {invite.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send invite email: {str(e)}")
            return False
    
    @staticmethod
    def resend_invite(invite):
        """Resend an existing invite"""
        try:
            if invite.status != 'pending':
                return {
                    'success': False,
                    'message': 'Only pending invites can be resent.'
                }
            
            # Extend expiry
            invite.expires_at = timezone.now() + timedelta(days=OrganizationInviteService.INVITE_EXPIRY_DAYS)
            invite.save(update_fields=['expires_at', 'updated_at'])
            
            # Send email
            email_sent = OrganizationInviteService._send_invite_email(invite)
            
            if email_sent:
                return {
                    'success': True,
                    'message': f'Invitation resent to {invite.email}'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to resend invitation email.'
                }
                
        except Exception as e:
            logger.error(f"Failed to resend invite: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while resending the invitation.'
            }
    
    @staticmethod
    def accept_invite(token, user=None, create_user_data=None):
        """Accept an organization invite"""
        try:
            # Find the invite
            try:
                invite = OrganizationInvite.objects.select_related('organization').get(token=token)
            except OrganizationInvite.DoesNotExist:
                return {
                    'success': False,
                    'message': 'Invalid invitation token.'
                }
            
            # Check if invite is valid
            if not invite.is_valid:
                if invite.is_expired:
                    invite.mark_expired()
                    return {
                        'success': False,
                        'message': 'This invitation has expired.'
                    }
                return {
                    'success': False,
                    'message': 'This invitation is no longer valid.'
                }
            
            with transaction.atomic():
                # If no user provided, check if user exists with invite email
                if not user:
                    user = User.objects.filter(email=invite.email).first()
                
                # If still no user and create_user_data provided, create new user
                if not user and create_user_data:
                    if not create_user_data.get('username') or not create_user_data.get('password'):
                        return {
                            'success': False,
                            'message': 'Username and password are required to create an account.'
                        }
                    
                    # Check if username exists
                    if User.objects.filter(username=create_user_data['username']).exists():
                        return {
                            'success': False,
                            'message': 'Username already exists.'
                        }
                    
                    user = User.objects.create_user(
                        username=create_user_data['username'],
                        email=invite.email,
                        password=create_user_data['password'],
                        first_name=create_user_data.get('first_name', ''),
                        last_name=create_user_data.get('last_name', '')
                    )
                
                if not user:
                    return {
                        'success': False,
                        'message': 'No user account found for this email. Please log in or create an account.',
                        'requires_registration': True
                    }
                
                # Check if user is already a member
                if OrganizationUser.objects.filter(
                    organization=invite.organization,
                    user=user,
                    is_active=True
                ).exists():
                    # Mark invite as accepted anyway
                    invite.mark_accepted(user)
                    return {
                        'success': False,
                        'message': 'You are already a member of this organization.'
                    }
                
                # Create the membership
                membership = OrganizationUser.objects.create(
                    organization=invite.organization,
                    user=user,
                    role=invite.role,
                    can_manage_farms=invite.can_manage_farms,
                    can_manage_users=invite.can_manage_users,
                    can_view_reports=invite.can_view_reports,
                    can_export_data=invite.can_export_data,
                    invited_by=invite.invited_by
                )
                
                # Mark invite as accepted
                invite.mark_accepted(user)
                
                logger.info(f"User {user.username} accepted invite to {invite.organization.name}")
                
                return {
                    'success': True,
                    'message': f'Welcome to {invite.organization.name}!',
                    'organization': invite.organization,
                    'membership': membership,
                    'user': user
                }
                
        except Exception as e:
            logger.error(f"Failed to accept invite: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while accepting the invitation.'
            }
    
    @staticmethod
    def get_invite_info(token):
        """Get invite information by token"""
        try:
            invite = OrganizationInvite.objects.select_related('organization', 'invited_by').get(token=token)
            
            # Check if there's an existing user with this email
            existing_user = User.objects.filter(email=invite.email).first()
            
            return {
                'success': True,
                'invite': invite,
                'organization_name': invite.organization.name,
                'email': invite.email,
                'role': invite.role,
                'is_valid': invite.is_valid,
                'is_expired': invite.is_expired,
                'status': invite.status,
                'has_existing_user': existing_user is not None,
                'invited_by': invite.invited_by.get_full_name() or invite.invited_by.username if invite.invited_by else None
            }
        except OrganizationInvite.DoesNotExist:
            return {
                'success': False,
                'message': 'Invalid invitation token.'
            }
    
    @staticmethod
    def cancel_invite(invite):
        """Cancel a pending invite"""
        try:
            if invite.status != 'pending':
                return {
                    'success': False,
                    'message': 'Only pending invites can be cancelled.'
                }
            
            invite.cancel()
            logger.info(f"Invite to {invite.email} for {invite.organization.name} was cancelled")
            
            return {
                'success': True,
                'message': 'Invitation cancelled successfully.'
            }
        except Exception as e:
            logger.error(f"Failed to cancel invite: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while cancelling the invitation.'
            }
    
    @staticmethod
    def get_pending_invites(organization):
        """Get all pending invites for an organization"""
        return OrganizationInvite.objects.filter(
            organization=organization,
            status='pending'
        ).select_related('invited_by').order_by('-created_at')
    
    @staticmethod
    def cleanup_expired_invites():
        """Mark expired invites as expired (called by scheduled task)"""
        expired_count = OrganizationInvite.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        ).update(status='expired')
        
        if expired_count > 0:
            logger.info(f"Marked {expired_count} invites as expired")
        
        return expired_count

