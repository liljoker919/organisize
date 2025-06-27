"""
Email preference and unsubscribe views for Organisize.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.utils import timezone
import logging

from .models import UserEmailPreference
from .email_utils import send_html_email, log_email

logger = logging.getLogger(__name__)


def unsubscribe_view(request, token):
    """
    Handle email unsubscribe requests via token.
    This allows users to unsubscribe even if they're not logged in.
    """
    try:
        preferences = UserEmailPreference.objects.get(unsubscribe_token=token)
        user = preferences.user
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'unsubscribe_all':
                preferences.unsubscribe_all()
                logger.info(f"User {user.username} ({user.email}) unsubscribed from all emails")
                
                # Send confirmation email
                send_unsubscribe_confirmation_email(user)
                
                messages.success(request, 
                    "You have been successfully unsubscribed from all email communications. "
                    "You will only receive essential security-related emails (like password resets).")
                
            elif action == 'update_preferences':
                # Update individual preferences
                preferences.receive_vacation_invitations = request.POST.get('receive_vacation_invitations') == 'on'
                preferences.receive_activity_notifications = request.POST.get('receive_activity_notifications') == 'on'
                preferences.receive_account_notifications = request.POST.get('receive_account_notifications') == 'on'
                preferences.receive_marketing_emails = request.POST.get('receive_marketing_emails') == 'on'
                preferences.save()
                
                logger.info(f"User {user.username} ({user.email}) updated email preferences")
                messages.success(request, "Your email preferences have been updated successfully.")
        
        context = {
            'user': user,
            'preferences': preferences,
            'token': token,
        }
        
        return render(request, 'emails/unsubscribe.html', context)
        
    except UserEmailPreference.DoesNotExist:
        logger.warning(f"Invalid unsubscribe token used: {token}")
        return render(request, 'emails/unsubscribe_invalid.html', status=404)


@login_required
def email_preferences_view(request):
    """
    Allow logged-in users to manage their email preferences.
    """
    preferences, created = UserEmailPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        preferences.receive_vacation_invitations = request.POST.get('receive_vacation_invitations') == 'on'
        preferences.receive_activity_notifications = request.POST.get('receive_activity_notifications') == 'on'
        preferences.receive_account_notifications = request.POST.get('receive_account_notifications') == 'on'
        preferences.receive_marketing_emails = request.POST.get('receive_marketing_emails') == 'on'
        
        # Handle resubscribe
        if request.POST.get('resubscribe') == 'true' and preferences.is_unsubscribed:
            preferences.unsubscribed_at = None
            logger.info(f"User {request.user.username} ({request.user.email}) resubscribed to emails")
        
        preferences.save()
        messages.success(request, "Your email preferences have been updated successfully.")
        return redirect('email_preferences')
    
    return render(request, 'planner/email_preferences.html', {'preferences': preferences})


def send_unsubscribe_confirmation_email(user):
    """
    Send confirmation email when user unsubscribes.
    """
    preferences = UserEmailPreference.objects.get(user=user)
    
    context = {
        'username': user.username,
        'user_email': user.email,
        'resubscribe_url': f"https://organisize.com/unsubscribe/{preferences.unsubscribe_token}/",
        'site_url': 'https://organisize.com',
    }
    
    # Send confirmation email (this bypasses preference checking since it's a confirmation)
    return send_html_email(
        subject="Organisize - Unsubscribe Confirmation",
        template_name="unsubscribe_confirmation",
        context=context,
        recipient_list=[user.email],
        email_type="unsubscribe_confirmation"
    )