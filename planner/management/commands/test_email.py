"""
Django management command to test email delivery for production environments.

This command provides an easy way to test email functionality with any SMTP
backend including AWS SES, SendGrid, Mailgun, etc.
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from planner.email_utils import send_html_email
import socket
from datetime import datetime


class Command(BaseCommand):
    help = 'Send test emails to verify SMTP configuration (AWS SES, SendGrid, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send test emails to'
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
        parser.add_argument(
            '--skip-config-check',
            action='store_true',
            help='Skip SMTP configuration validation'
        )

    def handle(self, *args, **options):
        email = options['email']
        basic_only = options['basic_only']
        html_only = options['html_only']
        skip_config_check = options['skip_config_check']
        
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        self.stdout.write(
            self.style.SUCCESS('Testing Email Delivery - Production SMTP')
        )
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        
        # Display current configuration
        self.stdout.write('\nCurrent email configuration:')
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {getattr(settings, "EMAIL_USE_TLS", "Not set")}')
        self.stdout.write(f'EMAIL_USE_SSL: {getattr(settings, "EMAIL_USE_SSL", "Not set")}')
        self.stdout.write(f'EMAIL_HOST_USER: {"[SET]" if settings.EMAIL_HOST_USER else "[NOT SET]"}')
        self.stdout.write(f'EMAIL_HOST_PASSWORD: {"[SET]" if settings.EMAIL_HOST_PASSWORD else "[NOT SET]"}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        # Validate configuration unless skipped
        if not skip_config_check:
            if not self.validate_smtp_config():
                self.stdout.write(
                    self.style.ERROR('\n❌ SMTP configuration validation failed. Use --skip-config-check to bypass.')
                )
                return
        
        self.stdout.write('\n' + '-' * 60)
        
        # Send test emails
        success_count = 0
        total_count = 0
        
        if not html_only:
            if self.send_basic_email(email):
                success_count += 1
            total_count += 1
        
        if not basic_only:
            if self.send_html_email(email):
                success_count += 1
            total_count += 1
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        if success_count == total_count:
            self.stdout.write(
                self.style.SUCCESS(f'✅ All {success_count} test emails sent successfully!')
            )
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Check your email inbox (including spam folder)')
            self.stdout.write('2. Verify email headers for correct DKIM/SPF/DMARC')
            self.stdout.write('3. Test with different recipient domains if needed')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Only {success_count}/{total_count} emails sent successfully')
            )
        self.stdout.write('=' * 60)

    def validate_smtp_config(self):
        """Validate SMTP configuration for production use."""
        self.stdout.write('\nValidating SMTP configuration...')
        
        errors = []
        warnings = []
        
        # Check backend
        if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                warnings.append('Using console backend - emails will be printed to console only')
            else:
                errors.append(f'EMAIL_BACKEND is {settings.EMAIL_BACKEND}, expected smtp.EmailBackend for production')
        
        # Check required settings
        if not settings.EMAIL_HOST:
            errors.append('EMAIL_HOST is not set')
        
        if not settings.EMAIL_HOST_USER:
            warnings.append('EMAIL_HOST_USER is not set (may be required for authenticated SMTP)')
        
        if not settings.EMAIL_HOST_PASSWORD:
            warnings.append('EMAIL_HOST_PASSWORD is not set (may be required for authenticated SMTP)')
        
        # Check SES-specific configuration
        if 'amazonaws.com' in settings.EMAIL_HOST:
            self.stdout.write('  📧 Detected AWS SES configuration')
            if settings.EMAIL_PORT not in [25, 587, 465]:
                warnings.append(f'EMAIL_PORT is {settings.EMAIL_PORT}, AWS SES typically uses 25, 587, or 465')
            if not getattr(settings, 'EMAIL_USE_TLS', False) and not getattr(settings, 'EMAIL_USE_SSL', False):
                errors.append('AWS SES requires EMAIL_USE_TLS=True or EMAIL_USE_SSL=True')
        
        # Check common SMTP ports and TLS/SSL settings
        if settings.EMAIL_PORT == 587 and not getattr(settings, 'EMAIL_USE_TLS', False):
            warnings.append('Port 587 typically requires EMAIL_USE_TLS=True')
        elif settings.EMAIL_PORT == 465 and not getattr(settings, 'EMAIL_USE_SSL', False):
            warnings.append('Port 465 typically requires EMAIL_USE_SSL=True')
        
        # Display validation results
        if warnings:
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'  ⚠️  {warning}'))
        
        if errors:
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  ❌ {error}'))
            return False
        
        self.stdout.write(self.style.SUCCESS('  ✅ SMTP configuration looks valid'))
        return True

    def send_basic_email(self, email):
        """Send a basic text email."""
        self.stdout.write('\nSending basic text email...')
        
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        try:
            result = send_mail(
                subject=f'Organisize Email Test - Basic ({hostname})',
                message=(
                    f'✅ Email delivery test successful!\n\n'
                    f'This is a test email sent from Organisize to verify SMTP configuration.\n\n'
                    f'Test details:\n'
                    f'- Sent to: {email}\n'
                    f'- From: {settings.DEFAULT_FROM_EMAIL}\n'
                    f'- Backend: {settings.EMAIL_BACKEND}\n'
                    f'- Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n'
                    f'- TLS: {getattr(settings, "EMAIL_USE_TLS", False)}\n'
                    f'- SSL: {getattr(settings, "EMAIL_USE_SSL", False)}\n'
                    f'- Timestamp: {timestamp}\n'
                    f'- Server: {hostname}\n\n'
                    f'If you received this email, your SMTP configuration is working correctly!\n\n'
                    f'Next steps:\n'
                    f'1. Check email headers for DKIM, SPF, and DMARC validation\n'
                    f'2. Test with different email providers (Gmail, Outlook, etc.)\n'
                    f'3. Verify emails don\'t land in spam folders\n\n'
                    f'-- The Organisize Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ Basic email sent successfully. Result: {result}')
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Failed to send basic email: {e}')
            )
            return False

    def send_html_email(self, email):
        """Send an HTML email using custom email utilities."""
        self.stdout.write('\nSending HTML email...')
        
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        context = {
            'username': 'Email Tester',
            'site_url': 'https://organisize.com',
            'user_email': email,
            'test_details': {
                'hostname': hostname,
                'timestamp': timestamp,
                'backend': settings.EMAIL_BACKEND,
                'host': f'{settings.EMAIL_HOST}:{settings.EMAIL_PORT}',
                'tls': getattr(settings, 'EMAIL_USE_TLS', False),
                'ssl': getattr(settings, 'EMAIL_USE_SSL', False),
            }
        }
        
        try:
            result = send_html_email(
                subject=f'Organisize Email Test - HTML ({hostname})',
                template_name='registration_confirmation',
                context=context,
                recipient_list=[email]
            )
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ HTML email sent successfully. Result: {result}')
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Failed to send HTML email: {e}')
            )
            return False