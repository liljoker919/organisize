"""
Django management command to process AWS SES complaint notifications.

This command processes complaint notifications from AWS SES and updates
user email preferences to prevent future emails to complained addresses.
"""

import json
import boto3
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from planner.models import EmailLog, UserEmailPreference
from planner.email_utils import get_or_create_email_preferences
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process AWS SES complaint notifications from SQS queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue-url',
            type=str,
            help='AWS SQS Queue URL for complaint notifications',
            default=getattr(settings, 'AWS_SES_COMPLAINT_QUEUE_URL', None)
        )
        parser.add_argument(
            '--region',
            type=str,
            help='AWS region',
            default=getattr(settings, 'AWS_DEFAULT_REGION', 'us-east-1')
        )
        parser.add_argument(
            '--max-messages',
            type=int,
            help='Maximum number of messages to process',
            default=10
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Process messages without making changes',
        )

    def handle(self, *args, **options):
        queue_url = options['queue_url']
        if not queue_url:
            raise CommandError(
                'Queue URL is required. Set AWS_SES_COMPLAINT_QUEUE_URL in settings '
                'or provide --queue-url argument.'
            )

        try:
            # Initialize SQS client
            sqs = boto3.client('sqs', region_name=options['region'])
            
            self.stdout.write(
                self.style.SUCCESS(f'Processing complaint notifications from {queue_url}')
            )
            
            processed_count = 0
            error_count = 0
            
            while processed_count < options['max_messages']:
                # Receive messages from SQS queue
                response = sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=min(10, options['max_messages'] - processed_count),
                    WaitTimeSeconds=5
                )
                
                messages = response.get('Messages', [])
                if not messages:
                    self.stdout.write('No more messages to process.')
                    break
                
                for message in messages:
                    try:
                        self.process_complaint_message(message, options['dry_run'])
                        processed_count += 1
                        
                        # Delete message from queue if not dry run
                        if not options['dry_run']:
                            sqs.delete_message(
                                QueueUrl=queue_url,
                                ReceiptHandle=message['ReceiptHandle']
                            )
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing message: {str(e)}")
                        self.stdout.write(
                            self.style.ERROR(f"Error processing message: {str(e)}")
                        )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {processed_count} messages, {error_count} errors'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Failed to process complaint notifications: {str(e)}')

    def process_complaint_message(self, message, dry_run=False):
        """Process a single complaint notification message."""
        try:
            # Parse the message body
            body = json.loads(message['Body'])
            
            # Handle SNS message format
            if 'Message' in body:
                sns_message = json.loads(body['Message'])
            else:
                sns_message = body
            
            # Extract complaint information
            if sns_message.get('notificationType') != 'Complaint':
                self.stdout.write(f"Skipping non-complaint notification: {sns_message.get('notificationType')}")
                return
            
            complaint = sns_message.get('complaint', {})
            complained_recipients = complaint.get('complainedRecipients', [])
            feedback_type = complaint.get('complaintFeedbackType')
            timestamp = complaint.get('timestamp')
            
            # Find original email log by SES message ID
            mail = sns_message.get('mail', {})
            ses_message_id = mail.get('messageId')
            
            self.stdout.write(
                self.style.WARNING(
                    f"Processing complaint: {feedback_type} for {len(complained_recipients)} recipients"
                )
            )
            
            for recipient in complained_recipients:
                email_address = recipient.get('emailAddress')
                if not email_address:
                    continue
                
                self.stdout.write(f"  - COMPLAINT: {email_address}")
                
                if dry_run:
                    self.stdout.write(f"    [DRY RUN] Would process complaint for {email_address}")
                    continue
                
                # Update email log if we can find it
                try:
                    email_logs = EmailLog.objects.filter(
                        ses_message_id=ses_message_id,
                        recipient_email=email_address
                    )
                    
                    for email_log in email_logs:
                        email_log.mark_complained(feedback_type)
                        logger.warning(f"Updated email log {email_log.id} for complaint")
                        
                except EmailLog.DoesNotExist:
                    # Create a complaint log entry even if we don't have the original
                    EmailLog.objects.create(
                        email_type='unknown',
                        recipient_email=email_address,
                        subject='Complaint notification',
                        status='complained',
                        ses_message_id=ses_message_id,
                        complaint_feedback_type=feedback_type
                    )
                    logger.warning(f"Created complaint log entry for {email_address}")
                
                # CRITICAL: Update user email preferences to stop all emails
                try:
                    user = User.objects.get(email=email_address)
                    preferences = get_or_create_email_preferences(user)
                    
                    # Mark as complained - this stops ALL email communication
                    preferences.mark_complaint()
                    
                    logger.critical(f"COMPLAINT: Disabled all emails for user {user.username} ({email_address})")
                    self.stdout.write(
                        self.style.ERROR(f"    DISABLED ALL EMAILS for user: {user.username}")
                    )
                    
                except User.DoesNotExist:
                    logger.warning(f"No user found for complained email: {email_address}")
                    self.stdout.write(f"    No user found for email: {email_address}")
                    
                    # Still need to track the complaint even without a user
                    # This prevents future registrations with this email
                    
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in message: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error processing complaint message: {str(e)}")