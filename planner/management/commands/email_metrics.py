"""
Django management command to monitor email sending metrics and generate reports.

This command analyzes email logs and provides insights into email
delivery performance, bounce rates, and complaint rates.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from planner.models import EmailLog, UserEmailPreference
from django.db.models import Count, Q
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate email delivery metrics and monitoring reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Number of days to analyze (default: 7)',
            default=7
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['text', 'csv', 'json'],
            help='Output format',
            default='text'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Include detailed breakdowns',
        )

    def handle(self, *args, **options):
        days = options['days']
        format_type = options['format']
        detailed = options['detailed']
        
        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Email Metrics Report - Last {days} days')
        )
        self.stdout.write('=' * 60)
        
        # Basic email statistics
        email_stats = self.get_email_statistics(start_date)
        self.display_basic_stats(email_stats)
        
        # Bounce and complaint rates
        rates = self.calculate_rates(start_date)
        self.display_rates(rates)
        
        # User email status overview
        user_stats = self.get_user_statistics()
        self.display_user_stats(user_stats)
        
        if detailed:
            # Email type breakdown
            type_breakdown = self.get_email_type_breakdown(start_date)
            self.display_type_breakdown(type_breakdown)
            
            # Recent bounces and complaints
            recent_issues = self.get_recent_issues(start_date)
            self.display_recent_issues(recent_issues)

    def get_email_statistics(self, start_date):
        """Get basic email sending statistics."""
        return {
            'total_sent': EmailLog.objects.filter(
                created_at__gte=start_date,
                status__in=['sent', 'delivered']
            ).count(),
            'total_delivered': EmailLog.objects.filter(
                created_at__gte=start_date,
                status='delivered'
            ).count(),
            'total_bounced': EmailLog.objects.filter(
                created_at__gte=start_date,
                status='bounced'
            ).count(),
            'total_complained': EmailLog.objects.filter(
                created_at__gte=start_date,
                status='complained'
            ).count(),
            'total_failed': EmailLog.objects.filter(
                created_at__gte=start_date,
                status='failed'
            ).count(),
            'total_pending': EmailLog.objects.filter(
                created_at__gte=start_date,
                status='pending'
            ).count(),
        }

    def calculate_rates(self, start_date):
        """Calculate bounce and complaint rates."""
        stats = self.get_email_statistics(start_date)
        total_attempts = EmailLog.objects.filter(created_at__gte=start_date).count()
        
        if total_attempts == 0:
            return {'bounce_rate': 0, 'complaint_rate': 0, 'success_rate': 0}
        
        return {
            'bounce_rate': (stats['total_bounced'] / total_attempts) * 100,
            'complaint_rate': (stats['total_complained'] / total_attempts) * 100,
            'success_rate': (stats['total_delivered'] / total_attempts) * 100,
        }

    def get_user_statistics(self):
        """Get user email preference statistics."""
        total_users = User.objects.count()
        preferences = UserEmailPreference.objects.all()
        
        return {
            'total_users': total_users,
            'users_with_preferences': preferences.count(),
            'unsubscribed_users': preferences.filter(unsubscribed_at__isnull=False).count(),
            'complained_users': preferences.filter(complaint_received=True).count(),
            'invalid_email_users': preferences.filter(is_email_valid=False).count(),
        }

    def get_email_type_breakdown(self, start_date):
        """Get breakdown by email type."""
        return EmailLog.objects.filter(
            created_at__gte=start_date
        ).values('email_type').annotate(
            count=Count('id'),
            sent=Count('id', filter=Q(status__in=['sent', 'delivered'])),
            bounced=Count('id', filter=Q(status='bounced')),
            complained=Count('id', filter=Q(status='complained')),
            failed=Count('id', filter=Q(status='failed'))
        ).order_by('-count')

    def get_recent_issues(self, start_date):
        """Get recent bounces and complaints."""
        return {
            'bounces': EmailLog.objects.filter(
                created_at__gte=start_date,
                status='bounced'
            ).order_by('-created_at')[:10],
            'complaints': EmailLog.objects.filter(
                created_at__gte=start_date,
                status='complained'
            ).order_by('-created_at')[:10],
        }

    def display_basic_stats(self, stats):
        """Display basic email statistics."""
        self.stdout.write(f"\n📧 Email Sending Statistics:")
        self.stdout.write(f"   Total Sent:      {stats['total_sent']:,}")
        self.stdout.write(f"   Delivered:       {stats['total_delivered']:,}")
        self.stdout.write(f"   Bounced:         {stats['total_bounced']:,}")
        self.stdout.write(f"   Complained:      {stats['total_complained']:,}")
        self.stdout.write(f"   Failed:          {stats['total_failed']:,}")
        self.stdout.write(f"   Pending:         {stats['total_pending']:,}")

    def display_rates(self, rates):
        """Display bounce and complaint rates."""
        self.stdout.write(f"\n📊 Delivery Rates:")
        self.stdout.write(f"   Success Rate:    {rates['success_rate']:.2f}%")
        self.stdout.write(f"   Bounce Rate:     {rates['bounce_rate']:.2f}% {'⚠️' if rates['bounce_rate'] > 5 else '✅'}")
        self.stdout.write(f"   Complaint Rate:  {rates['complaint_rate']:.2f}% {'⚠️' if rates['complaint_rate'] > 0.1 else '✅'}")
        
        # AWS SES guidelines warnings
        if rates['bounce_rate'] > 5:
            self.stdout.write(
                self.style.WARNING(
                    "   WARNING: Bounce rate exceeds 5% (AWS SES threshold)"
                )
            )
        
        if rates['complaint_rate'] > 0.1:
            self.stdout.write(
                self.style.ERROR(
                    "   CRITICAL: Complaint rate exceeds 0.1% (AWS SES threshold)"
                )
            )

    def display_user_stats(self, stats):
        """Display user statistics."""
        self.stdout.write(f"\n👥 User Email Status:")
        self.stdout.write(f"   Total Users:           {stats['total_users']:,}")
        self.stdout.write(f"   With Preferences:      {stats['users_with_preferences']:,}")
        self.stdout.write(f"   Unsubscribed:          {stats['unsubscribed_users']:,}")
        self.stdout.write(f"   Complained:            {stats['complained_users']:,}")
        self.stdout.write(f"   Invalid Email:         {stats['invalid_email_users']:,}")

    def display_type_breakdown(self, breakdown):
        """Display email type breakdown."""
        self.stdout.write(f"\n📋 Email Type Breakdown:")
        for item in breakdown:
            email_type = item['email_type']
            count = item['count']
            sent = item['sent']
            bounced = item['bounced']
            complained = item['complained']
            failed = item['failed']
            
            success_rate = (sent / count * 100) if count > 0 else 0
            
            self.stdout.write(f"   {email_type:20} | Total: {count:4} | Sent: {sent:4} | Success: {success_rate:5.1f}%")

    def display_recent_issues(self, issues):
        """Display recent bounces and complaints."""
        if issues['bounces']:
            self.stdout.write(f"\n🔄 Recent Bounces:")
            for bounce in issues['bounces']:
                self.stdout.write(f"   {bounce.created_at.strftime('%Y-%m-%d %H:%M')} | {bounce.recipient_email} | {bounce.bounce_type or 'Unknown'}")
        
        if issues['complaints']:
            self.stdout.write(f"\n⚠️  Recent Complaints:")
            for complaint in issues['complaints']:
                self.stdout.write(f"   {complaint.created_at.strftime('%Y-%m-%d %H:%M')} | {complaint.recipient_email} | {complaint.complaint_feedback_type or 'Unknown'}")