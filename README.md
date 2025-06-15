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

### Option 2: Docker Development Setup (Recommended)

For the best development experience with email testing, use Docker with MailHog:

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

#### Quick Start
1. Clone the repository:
```bash
git clone <repository-url>
cd organisize
```

2. Start the development environment:
```bash
docker-compose up
```

This will start:
- **Django app** at http://localhost:8000
- **MailHog** (email testing) at http://localhost:8025

#### Email Testing with MailHog

MailHog captures all outgoing emails in development so you can:
- View sent emails at http://localhost:8025
- Test email functionality without sending real emails
- See email content and formatting

#### Development Workflow

```bash
# Start services
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs web
docker-compose logs mailhog

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

#### Testing Email Delivery

After starting the Docker services, test email delivery:

```bash
# Method 1: Use the custom management command
docker-compose exec web python manage.py test_mailhog_email

# Method 2: Use Django's built-in sendtestemail command
docker-compose exec web python manage.py sendtestemail test@example.com

# Method 3: Test with specific email address
docker-compose exec web python manage.py test_mailhog_email --email your@email.com

# Method 4: Test only HTML emails
docker-compose exec web python manage.py test_mailhog_email --html-only
```

Then visit http://localhost:8025 to see the test emails in MailHog.

#### Troubleshooting Docker Setup

**DNS Resolution Issues**
If you encounter "Temporary failure in name resolution" errors when testing emails:

1. **Check container connectivity**:
```bash
docker-compose ps  # Ensure both containers are running
```

2. **Use IP address workaround**:
```bash
# Find MailHog container IP
docker inspect mailhog | grep IPAddress

# Update .env.dev with the IP address
EMAIL_HOST=172.18.0.2  # Replace with actual IP
```

3. **Alternative: Use host networking** (Linux only):
```bash
# Modify docker-compose.yml to add:
network_mode: "host"
```

4. **Restart services after configuration changes**:
```bash
docker-compose down && docker-compose up
```

**Common Issues**
- **Port conflicts**: Ensure ports 8000, 8025, and 1025 are not in use
- **Permission errors**: Make sure Docker has permission to bind to ports
- **Build failures**: Check that `requirements.txt` dependencies can be installed

#### Environment Configuration

The Docker setup uses `.env.dev` for development settings:
- `DEBUG=True`
- Email routing to MailHog
- Development-friendly configurations

For production, create a `.env` file with your production settings.

### Option 3: Native MailHog Installation (CI/Alternative)

If you prefer not to use Docker or are setting up CI/CD, you can install MailHog directly:

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

#### Configuration for Native MailHog

1. Copy the CI environment template:
```bash
cp .env.ci .env
```

2. Start MailHog in background:
```bash
mailhog > /dev/null 2>&1 &
```

3. Test email functionality:
```bash
python manage.py test_mailhog_email
```

4. View emails at http://localhost:8025

#### CI/CD Integration

The project includes automated CI testing with MailHog in GitHub Actions. The workflow:

1. Installs MailHog binary
2. Starts MailHog in background
3. Uses `.env.ci` configuration (localhost instead of Docker service name)
4. Tests email functionality before running the full test suite
5. Verifies emails are captured in MailHog via API

This approach is ideal for:
- Continuous Integration environments
- Environments where Docker is not available
- Minimal setup requirements

## Technology Stack

- Django 4.2.20
- Bootstrap 5.3.0
- SQLite (default database)
- Python 3.x
- Docker & Docker Compose (development)
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