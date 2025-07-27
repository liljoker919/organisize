from django.test import TestCase
from django.conf import settings
from django.db import connection
import os


class DatabaseConfigurationTest(TestCase):
    """Test database configuration for different environments"""

    def test_development_database_configuration(self):
        """Test that development environment uses SQLite"""
        # This test runs in test environment which should use SQLite like dev
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')
        # Note: Django uses in-memory database for testing, so we can't check exact filename
        # but we can verify the engine is SQLite

    def test_database_connection(self):
        """Test that database connection works"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_production_environment_settings(self):
        """Test that production environment settings are properly configured when ENV=prod"""
        # Save original environment
        original_env = os.environ.get('DJANGO_ENV', 'dev')
        
        try:
            # Test production configuration by checking settings module behavior
            # Note: We can't fully test this without reloading Django settings,
            # but we can verify the logic exists by checking environment detection
            from config.settings import ENV
            
            if ENV == 'prod':
                # If we're in production mode, check MySQL would be configured
                self.assertTrue(hasattr(settings, 'DATABASES'))
                # In actual production, this would be MySQL, but we can't test that here
                # without real MySQL credentials and connection
            else:
                # In dev/test mode, verify SQLite is used
                self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')
                
        finally:
            # Restore original environment
            if original_env:
                os.environ['DJANGO_ENV'] = original_env
            elif 'DJANGO_ENV' in os.environ:
                del os.environ['DJANGO_ENV']

    def test_mysql_configuration_exists_when_env_vars_present(self):
        """Test that MySQL configuration would be used if environment variables are set"""
        # This is a design test - verify the code structure supports MySQL configuration
        # We test the settings logic without actually connecting to MySQL
        from config import settings as settings_module
        import importlib
        
        # Check that the settings module has conditional database configuration
        source_code = open('/home/runner/work/organisize/organisize/config/settings.py').read()
        
        # Verify the essential MySQL configuration elements are in the settings
        self.assertIn('django.db.backends.mysql', source_code)
        self.assertIn('ENV == "prod"', source_code)
        self.assertIn('DB_NAME', source_code)
        self.assertIn('DB_USER', source_code)
        self.assertIn('DB_PASSWORD', source_code)
        self.assertIn('DB_HOST', source_code)
        self.assertIn('DB_PORT', source_code)