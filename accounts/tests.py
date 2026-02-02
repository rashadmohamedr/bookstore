from django.test import TestCase
from django.contrib.auth import get_user_model
# Create your tests here.

class CustomUserTests(TestCase):
    def test_create_user(self):
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
        self.assertFalse(user.is_staff)
    
    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
        username="rashadTestSuper", email="rashadTestSuper@email.com", password="passTest123"
        )
        self.assertEqual(admin_user.username, "rashadTestSuper")
        self.assertEqual(admin_user.email, "rashadTestSuper@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)