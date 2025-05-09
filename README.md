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

## Technology Stack

- Django 4.2.20
- Bootstrap 5.3.0
- SQLite (default database)
- Python 3.x

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

## Deployment

The project includes a GitHub Actions workflow for deployment to AWS Lightsail:

```yaml
name: Deploy to Lightsail
on:
  push:
    branches:
      - main
```

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