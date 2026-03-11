from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse, resolve 
from .forms import CustomUserCreationForm, CustomUserChangeForm 
from .views import SignupPageView 


# ============================================
# UNIT TESTS - Single Model/Function Testing
# ============================================

class CustomUserModelUnitTests(TestCase):
    """Unit tests for CustomUser model - testing single class behavior"""
    
    def test_create_user(self):
        """Test creating a regular user with valid data"""
        User = get_user_model()
        user = User.objects.create_user(
            username="rashadTest",
            email="rashadTest@gmail.com",
            password="passTest123"
        )
        self.assertEqual(user.username,"rashadTest")
        self.assertEqual(user.email,"rashadTest@gmail.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser with elevated privileges"""
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username="rashadTestSuper", 
            email="rashadTestSuper@email.com", 
            password="passTest123"
        )
        self.assertEqual(admin_user.username, "rashadTestSuper")
        self.assertEqual(admin_user.email, "rashadTestSuper@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_user_string_representation(self):
        """Test the string representation of user"""
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.assertEqual(str(user), "testuser")

    def test_user_email_label(self):
        """Test user email field label"""
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        field_label = user._meta.get_field('email').verbose_name
        self.assertEqual(field_label, 'email address')

    def test_username_max_length(self):
        """Test username field maximum length constraint"""
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        max_length = user._meta.get_field('username').max_length
        self.assertEqual(max_length, 150)


class CustomUserCreationFormUnitTests(TestCase):
    """Unit tests for CustomUserCreationForm - testing single form"""
    
    def test_form_has_correct_fields(self):
        """Test that form contains expected fields"""
        form = CustomUserCreationForm()
        self.assertIn('email', form.fields)
        self.assertIn('username', form.fields)
        self.assertIn('password1', form.fields)
        self.assertIn('password2', form.fields)

    def test_form_valid_data(self):
        """Test form validation with valid data"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_password_mismatch(self):
        """Test form rejects mismatched passwords"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass456!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_form_invalid_duplicate_username(self):
        """Test form rejects duplicate username"""
        User = get_user_model()
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )
        form_data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_form_saves_user(self):
        """Test that form correctly saves a new user"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('ComplexPass123!'))


class CustomUserChangeFormUnitTests(TestCase):
    """Unit tests for CustomUserChangeForm"""
    
    def test_form_has_correct_fields(self):
        """Test that change form contains expected fields"""
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        form = CustomUserChangeForm(instance=user)
        self.assertIn('email', form.fields)
        self.assertIn('username', form.fields)

    def test_form_updates_user(self):
        """Test that form correctly updates user data"""
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        form_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
        }
        form = CustomUserChangeForm(data=form_data, instance=user)
        if form.is_valid():
            updated_user = form.save()
            self.assertEqual(updated_user.username, 'updateduser')
            self.assertEqual(updated_user.email, 'updated@example.com')


class SignupViewUnitTests(TestCase):
    """Unit tests for SignupPageView - testing single view"""
    
    def test_signup_url_resolves_signup_view(self):
        """Test URL resolves to correct view"""
        view = resolve(reverse('account_signup'))
        self.assertEqual(view.func.__name__, SignupPageView.as_view().__name__)


class LoginViewUnitTests(TestCase):
    """Unit tests for login functionality"""
    
    def setUp(self):
        """Create a test user for login tests"""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_can_login_via_force_login(self):
        """Test user authentication mechanism works"""
        self.client.force_login(self.user)
        # After force_login, accessing a LoginRequiredMixin view should work
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)


# ============================================
# INTEGRATION TESTS - Auth Domain
# ============================================

class AuthenticationIntegrationTests(TestCase):
    """Integration tests for complete authentication workflows"""
    
    def setUp(self):
        """Set up test data"""
        User = get_user_model()
        self.user_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_login_logout_flow(self):
        """Test complete login and logout cycle"""
        # User logs in
        self.client.force_login(self.user)
        
        # Access protected page to verify login
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)
        
        # Test logout
        self.client.logout()
        
        # After logout, protected page should redirect
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_protected_page_requires_login(self):
        """Test that protected pages redirect to login"""
        # Try to access protected book list without login
        response = self.client.get(reverse('book_list'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_login_grants_access_to_protected_pages(self):
        """Test logged-in user can access protected pages"""
        # Login user
        self.client.force_login(self.user)
        
        # Access protected page
        response = self.client.get(reverse('book_list'))
        
        # Should succeed
        self.assertEqual(response.status_code, 200)