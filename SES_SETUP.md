# AWS SES Setup Guide for Organisize

This guide walks you through setting up Amazon Simple Email Service (SES) for transactional email delivery in your Organisize production environment.

## Prerequisites

- AWS account with billing set up
- Domain you own and can modify DNS records for
- Access to AWS Console and Route 53 (or your DNS provider)
- Django application with environment variable support

## Step 1: Set Up AWS SES

### 1.1 Access AWS SES Console
1. Log into your AWS Console
2. Navigate to **Simple Email Service (SES)**
3. Choose your preferred AWS region (e.g., us-east-1)

### 1.2 Verify Your Domain
1. In SES Console, go to **Configuration > Verified identities**
2. Click **Create identity**
3. Select **Domain** as identity type
4. Enter your domain (e.g., `organisize.com`)
5. Choose **Easy DKIM** (recommended)
6. Click **Create identity**

### 1.3 Configure DNS Records
AWS will provide DNS records that you need to add to your domain:

#### Required DNS Records:
1. **DKIM Records** (3 CNAME records)
   - These verify that emails are signed by your domain
   - Add all 3 CNAME records provided by AWS

2. **MX Record** (Optional but recommended)
   - Improves deliverability
   - Add if you don't have existing MX records

#### For Route 53:
If your domain uses Route 53, you can automatically add records:
1. In the verification details, click **Create records in Route 53**
2. Confirm the records creation

#### For Other DNS Providers:
1. Copy the DNS records from AWS SES console
2. Add them to your DNS provider (GoDaddy, Namecheap, Cloudflare, etc.)
3. Wait for DNS propagation (can take up to 72 hours)

### 1.4 Request Production Access
By default, SES starts in **sandbox mode** (can only send to verified emails):

1. In SES Console, go to **Account dashboard**
2. Click **Request production access**
3. Fill out the form:
   - **Mail type**: Transactional
   - **Website URL**: Your website URL
   - **Use case description**: 
     ```
     Transactional emails for Organisize vacation planning platform:
     - User registration confirmations
     - Password reset emails  
     - Vacation invitation emails
     - System notifications
     Expected volume: [your estimate] emails per day
     ```
4. Submit the request

**Note**: Production access approval usually takes 24-48 hours.

## Step 2: Create SMTP Credentials

### 2.1 Generate SMTP Credentials
1. In SES Console, go to **Configuration > SMTP settings**
2. Click **Create SMTP credentials**
3. Enter an IAM user name (e.g., `organisize-ses-smtp`)
4. Click **Create user**
5. **IMPORTANT**: Download and save the credentials - you won't see them again!

### 2.2 Note Your SMTP Settings
From the SMTP settings page, note:
- **SMTP endpoint**: `email-smtp.<region>.amazonaws.com`
- **Port**: 587 (TLS) or 465 (SSL)
- **Username**: From the downloaded credentials
- **Password**: From the downloaded credentials

## Step 3: Configure Django Settings

### 3.1 Update Environment Variables
Create or update your `.env` file:

```bash
# AWS SES Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_HOST_USER=YOUR_SES_SMTP_USERNAME
EMAIL_HOST_PASSWORD=YOUR_SES_SMTP_PASSWORD
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL="Organisize <noreply@yourdomain.com>"

# Optional: Set allowed hosts for production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Set DEBUG to false for production
DEBUG=false
```

**Important**: Replace:
- `us-east-1` with your chosen AWS region
- `YOUR_SES_SMTP_USERNAME` with the username from Step 2.1
- `YOUR_SES_SMTP_PASSWORD` with the password from Step 2.1  
- `yourdomain.com` with your actual domain

### 3.2 Verify Settings Are Loaded
The Django settings in `config/settings.py` already support all required environment variables:

```python
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@organisize.com")
```

## Step 4: Test Email Delivery

### 4.1 Basic Test
Use the provided management command to test email delivery:

```bash
# Test with a real email address
python manage.py test_email your-email@example.com

# Test only basic email
python manage.py test_email your-email@example.com --basic-only

# Test only HTML email  
python manage.py test_email your-email@example.com --html-only
```

### 4.2 Verify Email Headers
When you receive the test email:

1. **Check your inbox** (and spam folder)
2. **View email headers** to verify:
   - **DKIM-Signature**: Should show `d=yourdomain.com`
   - **Return-Path**: Should be from your domain
   - **Authentication-Results**: Should show DKIM pass

### 4.3 Test Different Providers
Test with email addresses from different providers:
- Gmail: `test+gmail@gmail.com`
- Outlook: `test+outlook@outlook.com` 
- Yahoo: `test+yahoo@yahoo.com`

## Step 5: Monitor and Maintain

### 5.1 Set Up CloudWatch Monitoring
1. In AWS SES Console, go to **Reputation tracking**
2. Monitor:
   - **Bounce rate** (keep under 5%)
   - **Complaint rate** (keep under 0.1%)
   - **Delivery metrics**

### 5.2 Handle Bounces and Complaints
Configure SNS notifications for bounces and complaints:

1. In SES Console, go to **Configuration > Configuration sets**
2. Create a configuration set for tracking
3. Set up SNS topics for bounce and complaint notifications

### 5.3 Domain Reputation
Monitor your domain reputation:
- Keep bounce rates low
- Handle unsubscribe requests promptly
- Use double opt-in for mailing lists
- Send only transactional emails through SES

## Troubleshooting

### Common Issues:

#### 1. Domain Not Verified
**Error**: `Email address not verified`
**Solution**: Ensure DNS records are properly configured and domain is verified

#### 2. Still in Sandbox Mode
**Error**: `Can only send to verified email addresses`
**Solution**: Request production access and wait for approval

#### 3. Authentication Failed
**Error**: `SMTP authentication failed`
**Solution**: Double-check SMTP username and password

#### 4. DNS Propagation
**Error**: Domain verification pending
**Solution**: Wait up to 72 hours for DNS propagation

#### 5. High Bounce Rate
**Error**: AWS throttling or suspending sending
**Solution**: Review email list quality and implement bounce handling

### Testing Commands:

```bash
# Test configuration validation
python manage.py test_email test@example.com

# Skip validation (useful for debugging)
python manage.py test_email test@example.com --skip-config-check

# Check Django's built-in test email
python manage.py sendtestemail test@example.com
```

## Security Best Practices

1. **Environment Variables**: Never commit SMTP credentials to code
2. **IAM Permissions**: Use minimal IAM permissions for SES SMTP user
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Monitoring**: Set up CloudWatch alarms for unusual activity
5. **Domain Authentication**: Always use DKIM and SPF records

## Cost Considerations

AWS SES pricing (as of 2024):
- **First 62,000 emails per month**: Free (for EC2-hosted applications)
- **Additional emails**: $0.10 per 1,000 emails
- **Data transfer**: Standard AWS rates apply

For most applications, SES is very cost-effective compared to other email services.

## Support Resources

- [AWS SES Documentation](https://docs.aws.amazon.com/ses/)
- [SES SMTP Interface](https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp.html)
- [SES Best Practices](https://docs.aws.amazon.com/ses/latest/dg/best-practices.html)
- [Django Email Documentation](https://docs.djangoproject.com/en/4.2/topics/email/)

## Next Steps

After successful SES setup:

1. **Test all email flows**:
   - User registration
   - Password reset
   - Vacation invitations

2. **Set up monitoring**:
   - CloudWatch dashboards
   - Bounce/complaint handling
   - Email delivery metrics

3. **Implement additional features**:
   - Email templates
   - Unsubscribe handling
   - Email preferences

4. **Consider scaling**:
   - Multiple domains
   - Dedicated IP addresses
   - Advanced reputation tracking