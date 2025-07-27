# MySQL Database Setup for Production

This document describes the MySQL database configuration for the Organisize.com production environment.

## Overview

The application now supports both SQLite (for development) and MySQL (for production) databases, with automatic configuration based on the `DJANGO_ENV` environment variable.

## Environment-Based Configuration

- **Development** (`DJANGO_ENV=dev` or not set): Uses SQLite database
- **Production** (`DJANGO_ENV=prod`): Uses MySQL database

## Production Database Configuration

### Required Environment Variables

The following environment variables must be set in the production environment:

```bash
DJANGO_ENV=prod
DB_NAME=organisize_db
DB_USER=dbmasteruser
DB_PASSWORD=<your_secure_password_here>
DB_HOST=ls-9c7c7dd27ff5739e45c3479dc63b4b0d9d6f7650.c3aomgso0h3s.us-east-2.rds.amazonaws.com
DB_PORT=3306
```

### AWS Lightsail MySQL Instance Details

- **Endpoint**: `ls-9c7c7dd27ff5739e45c3479dc63b4b0d9d6f7650.c3aomgso0h3s.us-east-2.rds.amazonaws.com`
- **Port**: `3306`
- **Database Name**: `organisize_db`
- **Username**: `dbmasteruser`
- **Password**: (to be set securely in production environment)

## Deployment Steps

### 1. Install Dependencies

Ensure `mysqlclient` is installed:

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Configure the production environment with the required database variables:

```bash
export DJANGO_ENV=prod
export DB_NAME=organisize_db
export DB_USER=dbmasteruser
export DB_PASSWORD=your_secure_password
export DB_HOST=ls-9c7c7dd27ff5739e45c3479dc63b4b0d9d6f7650.c3aomgso0h3s.us-east-2.rds.amazonaws.com
export DB_PORT=3306
```

### 3. Test Configuration

Verify the configuration is correct:

```bash
python manage.py check
```

### 4. Run Database Migrations

Run all migrations on the MySQL database:

```bash
python manage.py migrate
```

### 5. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

## Data Migration

Since the current SQLite database is empty (0 bytes), no data migration is required. All Django migrations will be applied to the fresh MySQL database.

## MySQL Configuration Details

The production MySQL configuration includes:

- **Engine**: `django.db.backends.mysql`
- **Charset**: `utf8mb4` (full Unicode support)
- **SQL Mode**: `STRICT_TRANS_TABLES` (strict mode for data integrity)
- **Connection pooling**: Standard Django database connection handling

## Security Features

- ✅ No hardcoded database credentials in source code
- ✅ All sensitive data loaded via environment variables
- ✅ DEBUG=False enforced in production
- ✅ MySQL strict mode enabled for data integrity
- ✅ UTF-8 Unicode support

## Troubleshooting

### Common Issues

1. **Connection refused**: Verify the AWS Lightsail instance is running and accessible
2. **Authentication failed**: Check that the password is correctly set
3. **Database not found**: Ensure the `organisize_db` database exists on the MySQL instance
4. **Permission denied**: Verify the `dbmasteruser` has the required privileges

### Testing Connectivity

To test database connectivity without running migrations:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT 1")
print("Database connection successful!")
```

### Logs

Check Django logs for database connection errors. The settings.py includes debug output showing the environment and configuration being loaded.

## Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Database Engine | SQLite | MySQL |
| Database File | `db.sqlite3` | AWS Lightsail |
| Configuration | `.env.dev` | `.env.prod` |
| DEBUG | True | False |
| Environment Variable | `DJANGO_ENV=dev` | `DJANGO_ENV=prod` |

## Next Steps

1. Set the secure MySQL password in the production environment
2. Test connectivity to the AWS Lightsail instance
3. Run `python manage.py migrate` to create all database tables
4. Deploy the application with the new configuration
5. Monitor database performance and connections

## Support

For issues with the MySQL database configuration or AWS Lightsail connectivity, check:

1. AWS Lightsail console for database status
2. Network connectivity from the production server
3. MySQL user permissions and database existence
4. Django error logs for specific connection errors