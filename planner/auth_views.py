"""
Custom authentication views for Organisize.
Extends Django's built-in views with enhanced email logging and security.
"""

from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template import loader
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

from .email_utils import send_password_reset_email, log_email

logger = logging.getLogger(__name__)


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form that uses our enhanced email system.
    """
    
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send the password reset email using our enhanced email system.
        """
        user = context['user']
        
        # Use our enhanced email function with logging
        result = send_password_reset_email(
            user=user,
            token=context['token'],
            uid=context['uid'],
            request=getattr(self, '_request', None)
        )
        
        logger.info(f"Password reset email sent to {user.email}: {result}")


class CustomPasswordResetView(auth_views.PasswordResetView):
    """
    Enhanced password reset view with improved logging and security.
    """
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    success_url = '/accounts/password_reset/done/'
    
    def form_valid(self, form):
        # Store request in form for email generation
        form._request = self.request
        
        # Log the password reset request
        logger.info(f"Password reset requested from IP {self.request.META.get('REMOTE_ADDR', 'unknown')}")
        
        return super().form_valid(form)


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    Enhanced password reset confirm view with logging.
    """
    template_name = 'registration/password_reset_confirm.html'
    success_url = '/accounts/reset/complete/'
    
    def form_valid(self, form):
        # Log successful password reset completion
        user = form.user
        logger.info(f"Password reset completed for user {user.username} ({user.email})")
        
        # Create email log entry for the completion
        log_email(
            email_type='password_reset',
            recipient_email=user.email,
            subject='Password Reset Completed',
            recipient_user=user,
            status='sent'
        )
        
        return super().form_valid(form)