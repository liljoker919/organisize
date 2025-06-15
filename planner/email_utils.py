"""
Email utilities for Organisize application.

This module provides helper functions for sending HTML emails
using Django's email framework with Bootstrap-styled templates.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def send_html_email(subject, template_name, context, recipient_list, from_email=None):
    """
    Send an HTML email using a template.
    
    Args:
        subject (str): Email subject line
        template_name (str): Path to HTML template (without .html extension)
        context (dict): Context variables for template rendering
        recipient_list (list): List of recipient email addresses
        from_email (str, optional): From email address
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
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
            to=recipient_list
        )
        
        # Attach HTML content
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        msg.send()
        
        logger.info(f"Email sent successfully to {recipient_list}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
        return False


def send_registration_confirmation_email(user, request=None):
    """
    Send registration confirmation email to a new user.
    
    Args:
        user: User instance
        request: Django request object (optional, for site URL)
    
    Returns:
        bool: True if email was sent successfully
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
        recipient_list=[user.email]
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
        bool: True if email was sent successfully
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
    }
    
    return send_html_email(
        subject=f"You're invited to join a vacation to {vacation.destination}!",
        template_name="vacation_invitation",
        context=context,
        recipient_list=[invitee_email]
    )