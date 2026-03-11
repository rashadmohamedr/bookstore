"""
Integration Tests for Bookstore Application
Tests the interaction between multiple domains/modules:
- Authentication + Books
- Users + Reviews
- Permissions + Access Control
- Search + Display
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from allauth.account.models import EmailAddress

from books.models import Book, Review
from books.forms import ReviewForm


class CompleteUserJourneyIntegrationTests(TestCase):
    """
    Integration tests for complete user journey through the application.
    Tests multiple domains working together: Auth, Books, Reviews, Permissions
    """
    
    def setUp(self):
        """Set up test data for user journey"""
        # Create permissions
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        
        # Create test books
        self.book1 = Book.objects.create(
            title="The Django Book",
            author="Adrian Holovaty",
            price="39.99",
        )
        self.book2 = Book.objects.create(
            title="Python Tricks",
            author="Dan Bader",
            price="29.99",
        )
    
    def test_new_user_signup_to_review_journey(self):
        """
        Test complete journey: 
        User created -> Login -> View books -> Get permission -> Read book -> Leave review
        """
        # Step 1: Create new user (simulating signup)
        User = get_user_model()
        user = User.objects.create_user(
            username='journeyuser',
            email='journey@example.com',
            password='ComplexPass123!'
        )
        
        # Step 2: User tries to access books (should work after login)
        self.client.force_login(user)
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Django Book')
        self.assertContains(response, 'Python Tricks')
        
        # Step 3: User tries to view book detail (should be denied - no permission)
        response = self.client.get(self.book1.get_absolute_url())
        self.assertEqual(response.status_code, 403)
        
        # Step 4: Admin grants user permission
        user.user_permissions.add(self.special_permission)
        
        # Step 5: User can now view book detail
        response = self.client.get(self.book1.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Django Book')
        
        # Step 6: User leaves a review
        review_data = {'review': 'Excellent book for learning Django!'}
        response = self.client.post(
            self.book1.get_absolute_url(),
            data=review_data,
            follow=True
        )
        
        # Step 7: Verify review was created and appears
        self.assertTrue(
            Review.objects.filter(
                book=self.book1,
                author=user,
                review='Excellent book for learning Django!'
            ).exists()
        )
        self.assertContains(response, 'Excellent book for learning Django!')
    
    def test_user_search_and_access_journey(self):
        """
        Test journey: Login -> Search for book -> View results -> Access book
        """
        # Create and login user with permissions
        User = get_user_model()
        user = User.objects.create_user(
            username='searchuser',
            email='search@example.com',
            password='testpass123'
        )
        user.user_permissions.add(self.special_permission)
        self.client.force_login(user)
        
        # Step 1: User searches for Django books
        response = self.client.get(reverse('search_results') + '?q=Django')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Django Book')
        self.assertNotContains(response, 'Python Tricks')
        
        # Step 2: User clicks on search result and views book
        response = self.client.get(self.book1.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Django Book')
        self.assertContains(response, 'Adrian Holovaty')


class MultiUserInteractionIntegrationTests(TestCase):
    """
    Integration tests for multiple users interacting with the same resources.
    Tests concurrency and data isolation.
    """
    
    def setUp(self):
        """Set up multiple users and shared book"""
        User = get_user_model()
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user1.user_permissions.add(self.special_permission)
        EmailAddress.objects.create(
            user=self.user1,
            email=self.user1.email,
            verified=True,
            primary=True
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user2.user_permissions.add(self.special_permission)
        EmailAddress.objects.create(
            user=self.user2,
            email=self.user2.email,
            verified=True,
            primary=True
        )
        
        # Create shared book
        self.book = Book.objects.create(
            title="Shared Book",
            author="Test Author",
            price="25.00",
        )
    
    def test_multiple_users_leave_reviews_independently(self):
        """Test multiple users can independently review the same book"""
        # User 1 leaves review
        self.client.force_login(self.user1)
        self.client.post(
            self.book.get_absolute_url(),
            data={'review': 'User 1 thinks this book is great!'}
        )
        self.client.logout()
        
        # User 2 leaves review
        self.client.force_login(self.user2)
        self.client.post(
            self.book.get_absolute_url(),
            data={'review': 'User 2 finds this book helpful!'}
        )
        
        # Verify both reviews exist
        reviews = Review.objects.filter(book=self.book)
        self.assertEqual(reviews.count(), 2)
        
        # Verify review authors are correct
        user1_review = reviews.get(author=self.user1)
        user2_review = reviews.get(author=self.user2)
        self.assertEqual(user1_review.review, 'User 1 thinks this book is great!')
        self.assertEqual(user2_review.review, 'User 2 finds this book helpful!')
        
        # Verify both reviews appear on book page
        response = self.client.get(self.book.get_absolute_url())
        self.assertContains(response, 'User 1 thinks this book is great!')
        self.assertContains(response, 'User 2 finds this book helpful!')
    
    def test_user_without_permission_cannot_see_other_users_reviews(self):
        """Test permission model prevents unauthorized access"""
        # User 1 with permission leaves review
        self.client.force_login(self.user1)
        self.client.post(
            self.book.get_absolute_url(),
            data={'review': 'This is a great book!'}
        )
        self.client.logout()
        
        # Create user 3 without permission
        User = get_user_model()
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # User 3 cannot access book detail
        self.client.force_login(user3)
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)


class PermissionSystemIntegrationTests(TestCase):
    """
    Integration tests for permission system across authentication and books.
    Tests Auth domain + Books domain + Permissions.
    """
    
    def setUp(self):
        """Set up users with different permission levels"""
        User = get_user_model()
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        
        # Regular user without special permission
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        # Premium user with special permission
        self.premium_user = User.objects.create_user(
            username='premium',
            email='premium@example.com',
            password='testpass123'
        )
        self.premium_user.user_permissions.add(self.special_permission)
        
        # Create test book
        self.book = Book.objects.create(
            title="Premium Content",
            author="Exclusive Author",
            price="99.99",
        )
    
    def test_permission_gates_book_detail_access(self):
        """Test permission system controls access to book details"""
        # Regular user cannot access
        self.client.force_login(self.regular_user)
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        
        # Premium user can access
        self.client.force_login(self.premium_user)
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Premium Content')
    
    def test_permission_upgrade_flow(self):
        """Test user can gain access after permission is granted"""
        self.client.force_login(self.regular_user)
        
        # Initially blocked
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)
        
        # Grant permission (simulating upgrade)
        self.regular_user.user_permissions.add(self.special_permission)
        
        # Now has access
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Premium Content')
    
    def test_permission_downgrade_flow(self):
        """Test access is revoked when permission is removed"""
        self.client.force_login(self.premium_user)
        
        # Initially has access
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        
        # Remove permission (simulating downgrade)
        self.premium_user.user_permissions.remove(self.special_permission)
        
        # No longer has access
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)


class SearchAndDisplayIntegrationTests(TestCase):
    """
    Integration tests for search functionality and display.
    Tests Search + Books + Display rendering.
    """
    
    def setUp(self):
        """Create diverse set of books for search testing"""
        self.books = [
            Book.objects.create(
                title="Learning Python",
                author="Mark Lutz",
                price="59.99",
            ),
            Book.objects.create(
                title="Python Cookbook",
                author="David Beazley",
                price="49.99",
            ),
            Book.objects.create(
                title="Django for Professionals",
                author="William Vincent",
                price="39.99",
            ),
            Book.objects.create(
                title="Django for APIs",
                author="William Vincent",
                price="39.99",
            ),
            Book.objects.create(
                title="Flask Web Development",
                author="Miguel Grinberg",
                price="44.99",
            ),
        ]
    
    def test_search_then_display_flow(self):
        """Test searching and then viewing results"""
        # Search for a unique author
        response = self.client.get(reverse('search_results') + '?q=Mark Lutz')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Learning Python')
        self.assertNotContains(response, 'Flask Web Development')
    
    def test_search_by_author_shows_all_books(self):
        """Test searching by author displays all their books"""
        response = self.client.get(reverse('search_results') + '?q=William Vincent')
        self.assertContains(response, 'Django for Professionals')
        self.assertContains(response, 'Django for APIs')
        self.assertNotContains(response, 'Python Cookbook')
    
    def test_search_with_special_characters(self):
        """Test search handles queries gracefully"""
        # Search with empty query
        response = self.client.get(reverse('search_results') + '?q=')
        self.assertEqual(response.status_code, 200)
    
    def test_case_insensitive_search(self):
        """Test search works regardless of case"""
        responses = [
            self.client.get(reverse('search_results') + '?q=python'),
            self.client.get(reverse('search_results') + '?q=PYTHON'),
            self.client.get(reverse('search_results') + '?q=PyThOn'),
        ]
        
        # All should find the same books
        for response in responses:
            self.assertContains(response, 'Learning Python')
            self.assertContains(response, 'Python Cookbook')


class ReviewWorkflowCompleteIntegrationTests(TestCase):
    """
    Integration tests for complete review workflow.
    Tests Auth + Books + Reviews + Forms working together.
    """
    
    def setUp(self):
        """Set up complete test environment"""
        User = get_user_model()
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
        self.user.user_permissions.add(self.special_permission)
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )
        
        self.book = Book.objects.create(
            title="Book to Review",
            author="Review Author",
            price="35.00",
        )
    
    def test_review_form_to_database_flow(self):
        """Test review form submission saves to database correctly"""
        self.client.force_login(self.user)
        
        # Submit review via form
        review_text = "This book changed my life!"
        response = self.client.post(
            self.book.get_absolute_url(),
            data={'review': review_text},
            follow=True
        )
        
        # Verify in database
        review = Review.objects.get(book=self.book, author=self.user)
        self.assertEqual(review.review, review_text)
        
        # Verify appears on page
        self.assertContains(response, review_text)
    
    def test_review_form_validation_integration(self):
        """Test form validation integrates with view correctly"""
        self.client.force_login(self.user)
        
        # Submit empty review
        response = self.client.post(
            self.book.get_absolute_url(),
            data={'review': ''},
            follow=True
        )
        
        # Should not create review
        self.assertFalse(
            Review.objects.filter(book=self.book, author=self.user).exists()
        )
    
    def test_multiple_reviews_same_user_different_books(self):
        """Test user can review multiple books"""
        self.client.force_login(self.user)
        
        # Create second book
        book2 = Book.objects.create(
            title="Another Book",
            author="Another Author",
            price="29.99",
        )
        
        # Review first book
        self.client.post(
            self.book.get_absolute_url(),
            data={'review': 'Review for book 1'}
        )
        
        # Review second book
        self.client.post(
            book2.get_absolute_url(),
            data={'review': 'Review for book 2'}
        )
        
        # Verify both reviews exist
        self.assertEqual(Review.objects.filter(author=self.user).count(), 2)
        
        # Verify reviews are on correct books
        review1 = Review.objects.get(book=self.book)
        review2 = Review.objects.get(book=book2)
        self.assertEqual(review1.review, 'Review for book 1')
        self.assertEqual(review2.review, 'Review for book 2')


class DataIntegrityIntegrationTests(TestCase):
    """
    Integration tests for data integrity across the system.
    Tests cascading deletes and relationship integrity.
    """
    
    def setUp(self):
        """Set up data with relationships"""
        User = get_user_model()
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        
        self.user = User.objects.create_user(
            username='datauser',
            email='data@example.com',
            password='testpass123'
        )
        self.user.user_permissions.add(self.special_permission)
        
        self.book = Book.objects.create(
            title="Relationship Test Book",
            author="Test Author",
            price="25.00",
        )
        
        self.review = Review.objects.create(
            book=self.book,
            author=self.user,
            review="Test review"
        )
    
    def test_deleting_book_cascades_to_reviews(self):
        """Test deleting book removes associated reviews"""
        book_id = self.book.id
        review_id = self.review.id
        
        # Delete book
        self.book.delete()
        
        # Book and review should be gone
        self.assertFalse(Book.objects.filter(id=book_id).exists())
        self.assertFalse(Review.objects.filter(id=review_id).exists())
    
    def test_deleting_user_cascades_to_reviews(self):
        """Test deleting user removes their reviews"""
        user_id = self.user.id
        review_id = self.review.id
        
        # Delete user
        self.user.delete()
        
        # User and review should be gone
        User = get_user_model()
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(Review.objects.filter(id=review_id).exists())
    
    def test_book_review_relationship_integrity(self):
        """Test book-review relationship maintains referential integrity"""
        # Verify relationship from book side
        book_reviews = self.book.reviews.all()
        self.assertEqual(book_reviews.count(), 1)
        self.assertEqual(book_reviews.first(), self.review)
        
        # Verify relationship from review side
        self.assertEqual(self.review.book, self.book)
        
        # Verify author relationship
        self.assertEqual(self.review.author, self.user)
