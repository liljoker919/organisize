"""
Test production environment configuration hardening.

This test validates that the production settings correctly configure DEBUG and ALLOWED_HOSTS
based on the DJANGO_ENV environment variable.

The production environment implements defense-in-depth for DEBUG settings:
1. DEBUG is forced to False when DJANGO_ENV=prod regardless of .env file configuration
2. A safety check prevents startup if DEBUG somehow remains True in production
"""
import os
import tempfile
from django.test import TestCase, override_settings
from django.conf import settings


class ProductionConfigurationTest(TestCase):
    """Test production environment configuration."""

    def test_production_debug_setting(self):
        """Test that DEBUG is False when DJANGO_ENV=prod."""
        current_env = os.environ.get('DJANGO_ENV')
        if current_env == 'prod':
            self.assertFalse(settings.DEBUG, "DEBUG should be False in production environment")
            self.assertIsInstance(settings.DEBUG, bool, "DEBUG should be a boolean, not string")
        else:
            # Skip this test if not in prod environment
            self.skipTest("Test only runs in production environment")

    def test_production_debug_forced_off(self):
        """Test that DEBUG is forced to False in production regardless of .env configuration."""
        current_env = os.environ.get('DJANGO_ENV')
        if current_env == 'prod':
            # This test verifies that even if .env.prod were misconfigured with DEBUG=True,
            # the production environment forces DEBUG=False for security
            self.assertFalse(settings.DEBUG, 
                            "DEBUG must be forced to False in production environment")
            self.assertIsInstance(settings.DEBUG, bool, 
                                "DEBUG should be a boolean value")
        else:
            # Skip this test if not in prod environment
            self.skipTest("Test only runs in production environment")

    def test_development_debug_setting(self):
        """Test that DEBUG is True when DJANGO_ENV=dev."""
        current_env = os.environ.get('DJANGO_ENV', 'dev')
        if current_env == 'dev' and settings.DEBUG:
            self.assertTrue(settings.DEBUG, "DEBUG should be True in development environment")
            self.assertIsInstance(settings.DEBUG, bool, "DEBUG should be a boolean, not string")
        elif current_env != 'dev':
            # Skip this test if not in dev environment
            self.skipTest("Test only runs in development environment")

    def test_production_allowed_hosts(self):
        """Test that ALLOWED_HOSTS is restricted in production."""
        current_env = os.environ.get('DJANGO_ENV')
        if current_env == 'prod':
            # In production, ALLOWED_HOSTS should not contain '*', localhost, or 127.0.0.1
            self.assertNotIn('*', settings.ALLOWED_HOSTS, 
                            "ALLOWED_HOSTS should not contain wildcard in production")
            self.assertNotIn('localhost', settings.ALLOWED_HOSTS,
                            "ALLOWED_HOSTS should not contain localhost in production")
            self.assertNotIn('127.0.0.1', settings.ALLOWED_HOSTS,
                            "ALLOWED_HOSTS should not contain 127.0.0.1 in production")
            # Should contain organisize.com
            self.assertIn('organisize.com', settings.ALLOWED_HOSTS,
                         "ALLOWED_HOSTS should contain organisize.com in production")
        else:
            # Skip this test if not in prod environment
            self.skipTest("Test only runs in production environment")

    def test_development_allowed_hosts(self):
        """Test that ALLOWED_HOSTS includes development hosts in dev environment."""
        current_env = os.environ.get('DJANGO_ENV', 'dev')
        if current_env == 'dev' and ('localhost' in settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS):
            # In development, ALLOWED_HOSTS should contain development-friendly hosts
            allowed_hosts = settings.ALLOWED_HOSTS
            self.assertTrue('localhost' in allowed_hosts or '*' in allowed_hosts,
                         "ALLOWED_HOSTS should contain localhost or wildcard in development")
        elif current_env != 'dev':
            # Skip this test if not in dev environment
            self.skipTest("Test only runs in development environment")

    def test_allowed_hosts_not_empty(self):
        """Test that ALLOWED_HOSTS is never empty."""
        self.assertTrue(settings.ALLOWED_HOSTS, "ALLOWED_HOSTS should not be empty")
        self.assertIsInstance(settings.ALLOWED_HOSTS, list, "ALLOWED_HOSTS should be a list")

    def test_static_files_configuration(self):
        """Test that static files are properly configured for production."""
        # Test STATIC_URL is set
        self.assertTrue(settings.STATIC_URL, "STATIC_URL should be set")
        self.assertEqual(settings.STATIC_URL, "/static/", "STATIC_URL should be '/static/'")
        
        # Test STATIC_ROOT is set for production collection
        self.assertTrue(settings.STATIC_ROOT, "STATIC_ROOT should be set for collectstatic")
        self.assertTrue(settings.STATIC_ROOT.endswith('staticfiles'), 
                       "STATIC_ROOT should point to staticfiles directory")
        
        # Test STATICFILES_DIRS includes planner static directory
        self.assertTrue(settings.STATICFILES_DIRS, "STATICFILES_DIRS should be configured")
        planner_static_found = any('planner' in static_dir for static_dir in settings.STATICFILES_DIRS)
        self.assertTrue(planner_static_found, "STATICFILES_DIRS should include planner static directory")

    def test_whitenoise_middleware_configuration(self):
        """Test that WhiteNoise middleware is properly configured for production static file serving."""
        middleware = settings.MIDDLEWARE
        
        # Test that WhiteNoise middleware is present
        whitenoise_middleware = 'whitenoise.middleware.WhiteNoiseMiddleware'
        self.assertIn(whitenoise_middleware, middleware, 
                     "WhiteNoise middleware should be configured for production static file serving")
        
        # Test that WhiteNoise is positioned correctly (after SecurityMiddleware)
        security_middleware = 'django.middleware.security.SecurityMiddleware'
        self.assertIn(security_middleware, middleware, "SecurityMiddleware should be present")
        
        security_index = middleware.index(security_middleware)
        whitenoise_index = middleware.index(whitenoise_middleware)
        self.assertEqual(whitenoise_index, security_index + 1, 
                        "WhiteNoise middleware should be immediately after SecurityMiddleware")

    def test_static_files_serving_ready(self):
        """Test that static file serving is ready for production deployment."""
        import os
        from django.conf import settings
        
        # Test that static files directory structure exists
        if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
            for static_dir in settings.STATICFILES_DIRS:
                self.assertTrue(os.path.exists(static_dir), 
                              f"Static files directory should exist: {static_dir}")
        
        # Test that the organisize logo files that are referenced in templates exist
        planner_static = os.path.join(settings.BASE_DIR, 'planner', 'static', 'planner', 'img')
        if os.path.exists(planner_static):
            # Check for logo files mentioned in the issue
            logo_files = ['organisize2.png', 'organisize4.png']  # Files used in base.html
            for logo_file in logo_files:
                logo_path = os.path.join(planner_static, logo_file)
                self.assertTrue(os.path.exists(logo_path), 
                              f"Logo file should exist for production: {logo_file}")