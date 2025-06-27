"""
Django management command to process AWS SES bounce notifications.

This command processes bounce notifications from AWS SES and updates
user email preferences and logs accordingly.
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
    help = 'Process AWS SES bounce notifications from SQS queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue-url',
            type=str,
            help='AWS SQS Queue URL for bounce notifications',
            default=getattr(settings, 'AWS_SES_BOUNCE_QUEUE_URL', None)
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
                'Queue URL is required. Set AWS_SES_BOUNCE_QUEUE_URL in settings '
                'or provide --queue-url argument.'
            )

        try:
            # Initialize SQS client
            sqs = boto3.client('sqs', region_name=options['region'])
            
            self.stdout.write(
                self.style.SUCCESS(f'Processing bounce notifications from {queue_url}')
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
                        self.process_bounce_message(message, options['dry_run'])
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
            raise CommandError(f'Failed to process bounce notifications: {str(e)}')

    def process_bounce_message(self, message, dry_run=False):
        """Process a single bounce notification message."""
        try:
            # Parse the message body
            body = json.loads(message['Body'])
            
            # Handle SNS message format
            if 'Message' in body:
                sns_message = json.loads(body['Message'])
            else:
                sns_message = body
            
            # Extract bounce information
            if sns_message.get('notificationType') != 'Bounce':
                self.stdout.write(f"Skipping non-bounce notification: {sns_message.get('notificationType')}")
                return
            
            bounce = sns_message.get('bounce', {})
            bounced_recipients = bounce.get('bouncedRecipients', [])
            bounce_type = bounce.get('bounceType')  # 'Permanent' or 'Transient'
            bounce_subtype = bounce.get('bounceSubType')
            timestamp = bounce.get('timestamp')
            
            # Find original email log by SES message ID
            mail = sns_message.get('mail', {})
            ses_message_id = mail.get('messageId')
            
            self.stdout.write(f"Processing bounce: {bounce_type}/{bounce_subtype} for {len(bounced_recipients)} recipients")
            
            for recipient in bounced_recipients:
                email_address = recipient.get('emailAddress')
                if not email_address:
                    continue
                
                self.stdout.write(f"  - {email_address}: {bounce_type}")
                
                if dry_run:
                    self.stdout.write(f"    [DRY RUN] Would process bounce for {email_address}")
                    continue
                
                # Update email log if we can find it
                try:
                    email_logs = EmailLog.objects.filter(
                        ses_message_id=ses_message_id,
                        recipient_email=email_address
                    )
                    
                    for email_log in email_logs:
                        email_log.mark_bounced(bounce_type, bounce_subtype)
                        logger.info(f"Updated email log {email_log.id} for bounce")
                        
                except EmailLog.DoesNotExist:
                    # Create a bounce log entry even if we don't have the original
                    EmailLog.objects.create(
                        email_type='unknown',
                        recipient_email=email_address,
                        subject='Bounce notification',
                        status='bounced',
                        ses_message_id=ses_message_id,
                        bounce_type=bounce_type,
                        bounce_subtype=bounce_subtype
                    )
                    logger.info(f"Created bounce log entry for {email_address}")
                
                # Update user email preferences
                try:
                    user = User.objects.get(email=email_address)
                    preferences = get_or_create_email_preferences(user)
                    
                    is_hard_bounce = bounce_type == 'Permanent'
                    preferences.mark_bounce(is_hard_bounce=is_hard_bounce)
                    
                    logger.info(f"Updated email preferences for user {user.username}")
                    self.stdout.write(f"    Updated preferences for user: {user.username}")
                    
                except User.DoesNotExist:
                    logger.warning(f"No user found for bounced email: {email_address}")
                    self.stdout.write(f"    No user found for email: {email_address}")
                    
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in message: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error processing bounce message: {str(e)}")