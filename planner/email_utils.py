"""
Email utilities for Organisize application.

This module provides helper functions for sending HTML emails
using Django's email framework with Bootstrap-styled templates.
Includes email preference checking, comprehensive logging, and
bounce/complaint handling for AWS SES compliance.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.contrib.auth.models import User
import logging
import uuid

logger = logging.getLogger(__name__)


def get_or_create_email_preferences(user):
    """Get or create email preferences for a user."""
    from .models import UserEmailPreference
    preferences, created = UserEmailPreference.objects.get_or_create(user=user)
    return preferences


def can_send_email(user, email_type='system'):
    """
    Check if we can send email to a user based on their preferences and status.
    
    Args:
        user: User instance
        email_type: Type of email ('vacation_invitation', 'activity_notification', etc.)
    
    Returns:
        tuple: (can_send: bool, reason: str)
    """
    if not user.email:
        return False, "No email address"
    
    preferences = get_or_create_email_preferences(user)
    
    if not preferences.can_receive_emails:
        return False, "User cannot receive emails (unsubscribed, complained, or invalid email)"
    
    # Check specific email type preferences
    email_type_map = {
        'vacation_invitation': preferences.receive_vacation_invitations,
        'activity_notification': preferences.receive_activity_notifications,
        'password_reset': preferences.receive_password_reset_emails,
        'registration': preferences.receive_account_notifications,
        'marketing': preferences.receive_marketing_emails,
        'system': preferences.receive_account_notifications,
    }
    
    if email_type in email_type_map and not email_type_map[email_type]:
        return False, f"User has disabled {email_type} emails"
    
    return True, "OK"


def log_email(email_type, recipient_email, subject, recipient_user=None, status='pending'):
    """
    Create an email log entry.
    
    Returns:
        EmailLog instance
    """
    from .models import EmailLog
    
    return EmailLog.objects.create(
        email_type=email_type,
        recipient_email=recipient_email,
        recipient_user=recipient_user,
        subject=subject,
        status=status
    )


def send_html_email(subject, template_name, context, recipient_list, from_email=None, email_type='system'):
    """
    Send an HTML email using a template with comprehensive logging and preference checking.
    
    Args:
        subject (str): Email subject line
        template_name (str): Path to HTML template (without .html extension)
        context (dict): Context variables for template rendering
        recipient_list (list): List of recipient email addresses
        from_email (str, optional): From email address
        email_type (str): Type of email for logging and preference checking
    
    Returns:
        dict: {'success': bool, 'sent_count': int, 'failed': list}
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    results = {'success': True, 'sent_count': 0, 'failed': []}
    
    for recipient_email in recipient_list:
        email_log = None
        
        try:
            # Find user by email if exists
            recipient_user = None
            try:
                recipient_user = User.objects.get(email=recipient_email)
            except User.DoesNotExist:
                pass
            
            # Create email log
            email_log = log_email(
                email_type=email_type,
                recipient_email=recipient_email,
                subject=subject,
                recipient_user=recipient_user
            )
            
            # Check if we can send to this user
            if recipient_user:
                can_send, reason = can_send_email(recipient_user, email_type)
                if not can_send:
                    email_log.mark_failed(f"Email blocked: {reason}")
                    logger.warning(f"Email blocked for {recipient_email}: {reason}")
                    results['failed'].append({'email': recipient_email, 'reason': reason})
                    continue
            
            # Add unsubscribe URL to context for user emails
            if recipient_user:
                preferences = get_or_create_email_preferences(recipient_user)
                context['unsubscribe_url'] = f"{context.get('site_url', 'https://organisize.com')}/unsubscribe/{preferences.unsubscribe_token}/"
                context['can_unsubscribe'] = True
            else:
                context['can_unsubscribe'] = False
            
            # Render HTML content
            html_content = render_to_string(f'emails/{template_name}.html', context)
            
            # Create plain text version by stripping HTML tags (basic fallback)
            import re
            text_content = re.sub(r'<[^>]+>', '', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email],
                headers={'X-Email-Type': email_type}
            )
            
            # Attach HTML content
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            
            # Update email log
            email_log.mark_sent()
            results['sent_count'] += 1
            
            # Update user's last email sent time
            if recipient_user:
                preferences = get_or_create_email_preferences(recipient_user)
                from django.utils import timezone
                preferences.last_email_sent = timezone.now()
                preferences.save()
            
            logger.info(f"Email sent successfully to {recipient_email}: {subject}")
            
        except Exception as e:
            error_msg = str(e)
            if email_log:
                email_log.mark_failed(error_msg)
            
            logger.error(f"Failed to send email to {recipient_email}: {error_msg}")
            results['failed'].append({'email': recipient_email, 'reason': error_msg})
            results['success'] = False
    
    return results


def send_registration_confirmation_email(user, request=None):
    """
    Send registration confirmation email to a new user.
    
    Args:
        user: User instance
        request: Django request object (optional, for site URL)
    
    Returns:
        dict: Email sending results
    """
    # Get site URL
    site_url = "https://organisize.com"  # Default
    if request:
        try:
            current_site = get_current_site(request)
            site_url = f"https://{current_site.domain}"
        except Exception:
            pass
    
    context = {
        'username': user.username,
        'user_email': user.email,
        'site_url': site_url,
    }
    
    return send_html_email(
        subject="Welcome to Organisize - Registration Successful!",
        template_name="registration_confirmation",
        context=context,
        recipient_list=[user.email],
        email_type="registration"
    )


def send_vacation_invitation_email(vacation, inviter, invitee_email, temp_password=None, request=None):
    """
    Send vacation invitation email.
    
    Args:
        vacation: VacationPlan instance
        inviter: User instance who sent the invitation
        invitee_email: Email address of the invitee
        temp_password: Temporary password for new users (optional)
        request: Django request object (optional, for URLs)
    
    Returns:
        dict: Email sending results
    """
    # Determine if this is a new user
    is_new_user = temp_password is not None
    
    # Build URLs
    login_url = "https://organisize.com/accounts/login/"
    vacation_url = f"https://organisize.com/vacations/{vacation.pk}/"
    
    if request:
        try:
            current_site = get_current_site(request)
            base_url = f"https://{current_site.domain}"
            login_url = f"{base_url}{reverse('login')}"
            vacation_url = f"{base_url}{reverse('vacation_detail', kwargs={'pk': vacation.pk})}"
        except Exception:
            pass
    
    context = {
        'vacation_destination': vacation.destination,
        'vacation_start_date': vacation.start_date.strftime('%B %d, %Y'),
        'vacation_end_date': vacation.end_date.strftime('%B %d, %Y'),
        'vacation_notes': vacation.notes,
        'inviter_name': inviter.get_full_name() or inviter.username,
        'user_email': invitee_email,
        'is_new_user': is_new_user,
        'temp_password': temp_password,
        'login_url': login_url,
        'vacation_url': vacation_url,
        'site_url': "https://organisize.com",
    }
    
    return send_html_email(
        subject=f"You're invited to join a vacation to {vacation.destination}!",
        template_name="vacation_invitation",
        context=context,
        recipient_list=[invitee_email],
        email_type="vacation_invitation"
    )


def send_password_reset_email(user, token, uid, request=None):
    """
    Send password reset email with enhanced logging.
    
    Args:
        user: User instance
        token: Password reset token
        uid: Encoded user ID
        request: Django request object (optional, for site URL)
    
    Returns:
        dict: Email sending results
    """
    # Get site URL
    site_url = "https://organisize.com"
    if request:
        try:
            current_site = get_current_site(request)
            site_url = f"{request.scheme}://{current_site.domain}"
        except Exception:
            pass
    
    # Build reset URL
    reset_url = f"{site_url}/accounts/reset/{uid}/{token}/"
    
    context = {
        'user': user,
        'username': user.username,
        'user_email': user.email,
        'reset_url': reset_url,
        'site_url': site_url,
        'domain': site_url.replace('https://', '').replace('http://', ''),
        'uid': uid,
        'token': token,
        'protocol': 'https',
    }
    
    return send_html_email(
        subject="Organisize - Password Reset Request",
        template_name="password_reset",
        context=context,
        recipient_list=[user.email],
        email_type="password_reset"
    )


def send_password_change_confirmation_email(user, request=None):
    """
    Send a confirmation email when a user changes their password.
    
    Args:
        user: User instance whose password was changed
        request: HttpRequest instance for context (optional)
    
    Returns:
        dict: Result from send_html_email
    """
    from django.utils import timezone
    
    # Get current site info
    site_url = "http://localhost:8000"  # fallback
    if request:
        try:
            current_site = get_current_site(request)
            site_url = f"{request.scheme}://{current_site.domain}"
        except Exception:
            pass
    
    context = {
        'user': user,
        'username': user.username,
        'user_email': user.email,
        'change_date': timezone.now(),
        'site_url': site_url,
        'domain': site_url.replace('https://', '').replace('http://', ''),
        'protocol': 'https',
    }
    
    return send_html_email(
        subject="Organisize - Password Changed Successfully",
        template_name="password_change_confirmation",
        context=context,
        recipient_list=[user.email],
        email_type="password_change"
    )