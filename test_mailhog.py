#!/usr/bin/env python
"""
Test script to verify email delivery to MailHog.

This script sends a test email using Django's email system
to verify that emails are being routed to MailHog correctly.

Usage:
    python test_mailhog.py

Make sure MailHog is running and accessible at EMAIL_HOST:EMAIL_PORT
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from planner.email_utils import send_html_email


def test_basic_email():
    """Test basic email sending with Django's send_mail."""
    print("Testing basic email with send_mail()...")
    
    try:
        result = send_mail(
            subject='MailHog Test - Basic Email',
            message='This is a test email sent to MailHog from Django.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        print(f"✅ Basic email sent successfully. Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Failed to send basic email: {e}")
        return False


def test_html_email():
    """Test HTML email sending with custom email utilities."""
    print("\nTesting HTML email with email_utils...")
    
    context = {
        'username': 'MailHog Tester',
        'site_url': 'http://localhost:8000',
        'user_email': 'test@example.com'
    }
    
    try:
        result = send_html_email(
            subject='MailHog Test - HTML Email',
            template_name='registration_confirmation',
            context=context,
            recipient_list=['test@example.com']
        )
        print(f"✅ HTML email sent successfully. Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Failed to send HTML email: {e}")
        return False


def main():
    """Run email tests and display configuration."""
    print("=" * 60)
    print("MailHog Email Delivery Test")
    print("=" * 60)
    
    # Display current email configuration
    print("\nCurrent email configuration:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check if we're using MailHog
    if settings.EMAIL_HOST != 'mailhog' and settings.EMAIL_HOST != '127.0.0.1':
        print(f"\n⚠️  Warning: EMAIL_HOST is '{settings.EMAIL_HOST}', expected 'mailhog' or '127.0.0.1'")
    
    if settings.EMAIL_PORT != 1025:
        print(f"⚠️  Warning: EMAIL_PORT is {settings.EMAIL_PORT}, expected 1025 for MailHog")
    
    print("\n" + "-" * 60)
    
    # Run tests
    basic_result = test_basic_email()
    html_result = test_html_email()
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print(f"Basic Email: {'✅ PASS' if basic_result else '❌ FAIL'}")
    print(f"HTML Email:  {'✅ PASS' if html_result else '❌ FAIL'}")
    
    if basic_result and html_result:
        print("\n🎉 All tests passed! Check MailHog at http://localhost:8025")
    else:
        print("\n💥 Some tests failed. Check your configuration and MailHog setup.")
    
    print("\nTo view sent emails:")
    print("1. Open your browser")
    print("2. Go to http://localhost:8025")
    print("3. You should see the test emails in the MailHog interface")
    print("=" * 60)


if __name__ == "__main__":
    main()