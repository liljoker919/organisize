"""
Django management command to test email delivery to MailHog.

This command provides an easy way to test email functionality
during development with MailHog.
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from planner.email_utils import send_html_email


class Command(BaseCommand):
    help = 'Send test emails to verify MailHog integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email address to send test emails to (default: test@example.com)'
        )
        parser.add_argument(
            '--basic-only',
            action='store_true',
            help='Send only basic text email'
        )
        parser.add_argument(
            '--html-only',
            action='store_true',
            help='Send only HTML email'
        )

    def handle(self, *args, **options):
        email = options['email']
        basic_only = options['basic_only']
        html_only = options['html_only']
        
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        self.stdout.write(
            self.style.SUCCESS('Testing Email Delivery to MailHog')
        )
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        
        # Display current configuration
        self.stdout.write('\nCurrent email configuration:')
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        # Check for MailHog configuration
        if settings.EMAIL_HOST != 'mailhog' and settings.EMAIL_HOST != '127.0.0.1':
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Warning: EMAIL_HOST is "{settings.EMAIL_HOST}", '
                    'expected "mailhog" or "127.0.0.1" for MailHog'
                )
            )
        
        if settings.EMAIL_PORT != 1025:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Warning: EMAIL_PORT is {settings.EMAIL_PORT}, '
                    'expected 1025 for MailHog'
                )
            )
        
        self.stdout.write('\n' + '-' * 60)
        
        # Send test emails
        if not html_only:
            self.send_basic_email(email)
        
        if not basic_only:
            self.send_html_email(email)
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS('Test emails sent successfully!')
        )
        self.stdout.write('\nTo view sent emails:')
        self.stdout.write('1. Open your browser')
        self.stdout.write('2. Go to http://localhost:8025')
        self.stdout.write('3. You should see the test emails in MailHog')
        self.stdout.write('=' * 60)

    def send_basic_email(self, email):
        """Send a basic text email."""
        self.stdout.write('\nSending basic text email...')
        
        try:
            result = send_mail(
                subject='MailHog Test - Basic Email from Django Management Command',
                message=(
                    'This is a test email sent to MailHog from Django.\n\n'
                    'If you can see this in MailHog at http://localhost:8025, '
                    'then your email configuration is working correctly!\n\n'
                    'Test details:\n'
                    f'- Sent to: {email}\n'
                    f'- From: {settings.DEFAULT_FROM_EMAIL}\n'
                    f'- Backend: {settings.EMAIL_BACKEND}\n'
                    f'- Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Basic email sent successfully. Result: {result}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send basic email: {e}')
            )

    def send_html_email(self, email):
        """Send an HTML email using custom email utilities."""
        self.stdout.write('\nSending HTML email...')
        
        context = {
            'username': 'Django Developer',
            'site_url': 'http://localhost:8000',
            'user_email': email
        }
        
        try:
            result = send_html_email(
                subject='MailHog Test - HTML Email from Django Management Command',
                template_name='registration_confirmation',
                context=context,
                recipient_list=[email]
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ HTML email sent successfully. Result: {result}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send HTML email: {e}')
            )