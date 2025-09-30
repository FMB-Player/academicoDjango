from django.test import TestCase, Client
from django.urls import reverse
from core.models import Usuario

class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test user with required fields for Persona and Usuario
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            dni=98765432,  # Required by Persona
            nombre='Test',  # Required by Persona
            apellido='User',  # Required by Persona
            rol=Usuario.Rol.ADMIN  # Admin role
        )

    def test_home_view_unauthorized(self):
        """Test home view is accessible to all users"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_view_authorized(self):
        """Test home view renders for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_dashboard_view_redirects_unauthorized(self):
        """Test dashboard redirects to login when not authenticated"""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        # Should redirect to login with 'next' parameter
        self.assertIn('/accounts/login/?next=/dashboard/', response.url)

    def test_admin_dashboard_access(self):
        """Test admin dashboard access with proper role"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('core:admin_dashboard'))
        # Should be 200 if user has admin role
        self.assertEqual(response.status_code, 200)
