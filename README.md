# Organisize - Vacation Planning Made Easy

Plan, organize, and manage your vacations seamlessly.

## Features

- **Vacation Management**
  - Create and edit vacation plans
  - Track planned vs booked trips
  - Manage estimated and actual costs
  - Add notes and track who's going

- **Travel Details**
  - Add and manage flight information
  - Track lodging reservations
  - Plan activities with schedules

- **Collaboration**
  - Share vacation plans with other users
  - Group planning functionality
  - View shared vacations in your dashboard

- **User Authentication**
  - Secure login and authentication
  - Personal dashboard for each user
  - Access control for shared vacations

## Installation

### Option 1: Standard Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd organisize
```
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

### Option 2: Native MailHog Installation (Recommended for Email Testing)

For the best development experience with email testing, install MailHog directly:

#### Installing MailHog

**Linux/macOS:**
```bash
# Download MailHog binary
wget -O mailhog https://github.com/mailhog/MailHog/releases/download/v1.0.1/MailHog_linux_amd64
chmod +x mailhog
sudo mv mailhog /usr/local/bin/

# Start MailHog
mailhog
```

**Using Go (cross-platform):**
```bash
go install github.com/mailhog/MailHog@latest
MailHog
```

#### Development Setup with MailHog

1. Clone the repository:
```bash
git clone <repository-url>
cd organisize
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the development environment template:
```bash
cp .env.dev .env
```

5. Start MailHog in background:
```bash
mailhog > /dev/null 2>&1 &
```

6. Apply database migrations:
```bash
python manage.py migrate
```

7. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

This will start:
- **Django app** at http://localhost:8000
- **MailHog** (email testing) at http://localhost:8025

#### Email Testing with MailHog

MailHog captures all outgoing emails in development so you can:
- View sent emails at http://localhost:8025
- Test email functionality without sending real emails
- See email content and formatting

#### Testing Email Delivery

After starting MailHog and the Django server, test email delivery:

```bash
# Method 1: Use the custom management command
python manage.py test_mailhog_email

# Method 2: Use Django's built-in sendtestemail command
python manage.py sendtestemail test@example.com

# Method 3: Test with specific email address
python manage.py test_mailhog_email --email your@email.com

# Method 4: Test only HTML emails
python manage.py test_mailhog_email --html-only
```

Then visit http://localhost:8025 to see the test emails in MailHog.

### Option 3: Alternative Setup for CI/CD

If you are setting up CI/CD or prefer an alternative configuration approach, you can use the CI environment setup:

#### Configuration for CI/Alternative Setup

1. Copy the CI environment template:
```bash
cp .env.ci .env
```

2. Install MailHog (see Option 2 for installation instructions)

3. Start MailHog in background:
```bash
mailhog > /dev/null 2>&1 &
```

4. Test email functionality:
```bash
python manage.py test_mailhog_email
```

5. View emails at http://localhost:8025

#### CI/CD Integration

The project includes automated CI testing with MailHog in GitHub Actions. The workflow:

1. Installs MailHog binary
2. Starts MailHog in background
3. Uses `.env.ci` configuration (localhost configuration)
4. Tests email functionality before running the full test suite
5. Verifies emails are captured in MailHog via API

This approach is ideal for:
- Continuous Integration environments
- Consistent development setup across team members
- Minimal setup requirements

## Technology Stack

- Django 4.2.20
- Bootstrap 5.3.0
- SQLite (default database)
- Python 3.x
- MailHog (email testing)

## Project Structure

```
organisize/
├── config/             # Project configuration
├── planner/           # Main application
│   ├── models.py      # Database models
│   ├── views.py       # View logic
│   ├── forms.py       # Form definitions
│   └── templates/     # HTML templates
├── templates/         # Global templates
└── manage.py         # Django management script
```

## Development

- The project uses Django's built-in authentication system
- Bootstrap is included via CDN for styling
- Model structure includes:
  - VacationPlan
  - Flight
  - Lodging
  - Activity
  - Group (for collaboration)

### Running Tests

The project includes comprehensive automated testing to ensure code quality and prevent regressions.

#### Quick Test Run
```bash
# Run all tests
python manage.py test

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML coverage report
```

#### Using the Test Runner Script
```bash
# Run the automated test script
./run_tests.sh
```

#### Test Structure
- **Model Tests**: Validate database models and their relationships
- **Form Tests**: Ensure form validation works correctly
- **View Tests**: Test view functionality and authentication
- **URL Tests**: Verify URL routing and resolution

#### Coverage Requirements
The test suite aims for high coverage of:
- All model methods and validations
- Form validation logic
- View authentication and responses
- URL routing

View coverage reports in `htmlcov/index.html` after running coverage.

## Deployment

The project includes a GitHub Actions workflow for automated deployment to AWS Lightsail with integrated testing:

### GitHub Actions Workflow

```yaml
name: Deploy to Lightsail
on:
  push:
    branches:
      - main

jobs:
  test:
    # Run comprehensive test suite with coverage
    
  deploy:
    needs: test  # Deployment only runs if tests pass
    # Deploy to AWS Lightsail
```

### Test Automation Features

- **Automated Testing**: All tests run on every push to main branch
- **Coverage Reporting**: Track test coverage across the codebase
- **Deployment Blocking**: Failed tests prevent deployment to production
- **Comprehensive Test Suite**: Tests models, views, forms, and URL routing

### Manual Deployment

If you need to deploy manually (not recommended for production):

1. SSH into your Lightsail instance
2. Navigate to the project directory
3. Run the test suite: `./run_tests.sh`
4. If tests pass, proceed with deployment steps

### Test-Driven Deployment Process

1. Developer pushes code to main branch
2. GitHub Actions triggers automated test suite
3. If tests fail, deployment is blocked and team is notified
4. If tests pass, deployment proceeds automatically
5. Production environment updated with tested code

## Authentication

- Login URL: `/accounts/login/`
- Logout URL: `/accounts/logout/`
- Default redirect after login: `vacation_list`

## License

All rights reserved. © Organisize

## Contributing

Currently, this is a private project and not open for public contributions.

## Security Notice

This is a development setup. For production:
- Change the SECRET_KEY
- Set DEBUG=False
- Configure proper ALLOWED_HOSTS
- Use a production-grade database
- Set up proper static files serving