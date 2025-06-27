# Email Workflows Implementation Guide

This document provides an overview of the comprehensive email workflows implemented for Organisize, ensuring AWS SES compliance and enhanced user experience.

## 🎯 Overview

The implementation includes four core email workflows:

1. **Enhanced Password Reset** - Secure password reset with logging
2. **Unsubscribe System** - Granular email preferences and opt-out management
3. **Bounce/Complaint Handling** - Automated AWS SES notification processing
4. **Email Logging & Monitoring** - Comprehensive tracking and analytics

## 📊 Features Implemented

### Password Reset Workflow ✅

- **Enhanced Django Views**: Custom password reset views with enhanced logging
- **Security Features**: Token validation, expiration tracking, IP logging
- **Custom Templates**: Bootstrap-styled email templates with security information
- **Logging**: Complete audit trail of password reset requests and completions

**Files**: `planner/auth_views.py`, `templates/emails/password_reset.html`

### Unsubscribe System ✅

- **User Preferences**: Granular control over email types
  - Vacation invitations
  - Activity notifications  
  - Account notifications
  - Marketing emails
- **Token-based Unsubscribe**: Works without requiring user login
- **Preference Management**: Web interface for users to manage preferences
- **Automatic Links**: All emails include unsubscribe links

**Files**: `planner/email_views.py`, `planner/models.py` (UserEmailPreference), `templates/emails/unsubscribe*.html`

### Bounce & Complaint Handling ✅

- **Real-time Processing**: Management commands to process AWS SES notifications
- **Automatic Suppression**: Invalid emails automatically disabled
- **Compliance**: Meets AWS SES bounce (5%) and complaint (0.1%) thresholds
- **User Protection**: Complaints immediately stop all communications

**Files**: `planner/management/commands/process_bounces.py`, `planner/management/commands/process_complaints.py`

### Email Logging & Monitoring ✅

- **Comprehensive Tracking**: All email sends logged with status updates
- **AWS SES Integration**: Message ID tracking, delivery confirmations
- **Analytics**: Email metrics and monitoring reports
- **Performance Monitoring**: Bounce rates, complaint rates, success rates

**Files**: `planner/models.py` (EmailLog), `planner/management/commands/email_metrics.py`

## 🚀 Usage

### Management Commands

```bash
# Process bounce notifications from SQS
python manage.py process_bounces --queue-url https://sqs.region.amazonaws.com/account/bounce-queue

# Process complaint notifications from SQS  
python manage.py process_complaints --queue-url https://sqs.region.amazonaws.com/account/complaint-queue

# Generate email metrics report
python manage.py email_metrics --days 7 --detailed

# Test email functionality
python manage.py test_email user@example.com
```

### URL Endpoints

```python
# Unsubscribe management
/unsubscribe/<token>/                    # Token-based unsubscribe
/vacations/email-preferences/            # User preference management (login required)

# Enhanced password reset
/accounts/password_reset/                # Enhanced password reset form
/accounts/reset/<uidb64>/<token>/        # Password reset confirmation with logging
```

### Email Preference Checking

```python
from planner.email_utils import can_send_email

# Check if user can receive specific email type
can_send, reason = can_send_email(user, 'vacation_invitation')
if can_send:
    # Send email
    pass
else:
    # Log why email was blocked
    logger.info(f"Email blocked: {reason}")
```

### Enhanced Email Sending

```python
from planner.email_utils import send_html_email

# Send email with automatic preference checking and logging
result = send_html_email(
    subject="Your Subject",
    template_name="your_template",
    context={'user': user},
    recipient_list=[user.email],
    email_type="vacation_invitation"
)

# Result includes detailed information
print(f"Success: {result['success']}")
print(f"Sent: {result['sent_count']}")
print(f"Failed: {len(result['failed'])}")
```

## 🔧 Configuration

### Environment Variables

```bash
# AWS SES Configuration (add to .env)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-ses-smtp-username
EMAIL_HOST_PASSWORD=your-ses-smtp-password
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL="Organisize <noreply@yourdomain.com>"

# AWS SQS Queue URLs for bounce/complaint processing
AWS_SES_BOUNCE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/account/bounce-queue
AWS_SES_COMPLAINT_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/account/complaint-queue
AWS_DEFAULT_REGION=us-east-1
```

### AWS SES Setup

1. **Configure SNS Topics**: Create topics for bounce and complaint notifications
2. **Setup SQS Queues**: Create queues subscribed to SNS topics
3. **Configuration Sets**: Use SES configuration sets for tracking
4. **Event Publishing**: Enable bounce and complaint event publishing

See `SES_SETUP.md` for detailed AWS configuration instructions.

## 📈 Monitoring & Analytics

### Key Metrics Tracked

- **Email Send Rate**: Total emails sent per day/week/month
- **Delivery Rate**: Percentage of emails successfully delivered
- **Bounce Rate**: Must stay under 5% (AWS SES requirement)
- **Complaint Rate**: Must stay under 0.1% (AWS SES requirement)
- **User Engagement**: Unsubscribe rates, preference changes

### Monitoring Commands

```bash
# Daily monitoring (recommended cron job)
python manage.py email_metrics --days 1

# Weekly detailed report
python manage.py email_metrics --days 7 --detailed

# Monitor AWS SES compliance
python manage.py email_metrics --days 30 | grep -E "(Bounce|Complaint) Rate"
```

## 🧪 Testing

### Test Suite

- **119 Total Tests**: All existing functionality + 14 new email workflow tests
- **Email Preference Tests**: User preference management and validation
- **Unsubscribe Tests**: Token-based unsubscribe functionality  
- **Email Logging Tests**: Comprehensive email tracking
- **Bounce/Complaint Tests**: AWS SES notification processing

```bash
# Run all tests
python manage.py test

# Run only email workflow tests  
python manage.py test planner.test_email_workflows

# Run with coverage
coverage run manage.py test && coverage report
```

## 🔒 Security & Compliance

### AWS SES Compliance

- ✅ **Bounce Rate Monitoring**: Automatic tracking and alerts
- ✅ **Complaint Handling**: Immediate suppression of complained addresses
- ✅ **Sender Reputation**: Proactive management to maintain good standing
- ✅ **List Hygiene**: Automatic removal of invalid/bounced addresses

### Privacy & User Rights

- ✅ **Easy Unsubscribe**: One-click unsubscribe with confirmation
- ✅ **Granular Preferences**: Users control what emails they receive
- ✅ **Data Protection**: Secure token-based preference management
- ✅ **Audit Trail**: Complete logging of all email activities

### Security Features

- ✅ **Token Validation**: Secure UUID-based unsubscribe tokens
- ✅ **Password Reset Security**: Enhanced logging and validation
- ✅ **IP Tracking**: Request source tracking for security monitoring
- ✅ **Rate Limiting**: Built-in protection against abuse

## 🚀 Production Deployment

### Pre-deployment Checklist

1. ✅ Configure AWS SES with verified domain
2. ✅ Set up SNS topics and SQS queues
3. ✅ Configure environment variables
4. ✅ Run database migrations
5. ✅ Test email delivery
6. ✅ Set up monitoring cron jobs

### Recommended Cron Jobs

```bash
# Process bounces every 5 minutes
*/5 * * * * cd /app && python manage.py process_bounces --max-messages 50

# Process complaints every 5 minutes  
*/5 * * * * cd /app && python manage.py process_complaints --max-messages 50

# Daily email metrics report
0 9 * * * cd /app && python manage.py email_metrics --days 1 > /var/log/email-metrics.log

# Weekly detailed report
0 9 * * 1 cd /app && python manage.py email_metrics --days 7 --detailed | mail -s "Weekly Email Report" admin@yourdomain.com
```

## 📚 Additional Resources

- [AWS SES Best Practices](https://docs.aws.amazon.com/ses/latest/dg/best-practices.html)
- [Django Email Documentation](https://docs.djangoproject.com/en/4.2/topics/email/)
- [AWS SES Event Publishing](https://docs.aws.amazon.com/ses/latest/dg/event-publishing.html)
- [Email Deliverability Guide](https://aws.amazon.com/ses/email-deliverability/)

## 💡 Next Steps

1. **AWS Lambda Integration**: Deploy real-time processing functions
2. **Email Templates**: Expand template library with more designs
3. **A/B Testing**: Implement email template testing
4. **Advanced Analytics**: Dashboard for email performance metrics
5. **Internationalization**: Multi-language email templates