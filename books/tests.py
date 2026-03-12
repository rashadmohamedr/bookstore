from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, RequestFactory
from django.urls import reverse, reverse_lazy
from decimal import Decimal
from allauth.account.models import EmailAddress
from .models import Book, Review, Cart, CartItem
from .forms import ReviewForm, AddToCartForm, UpdateCartItemForm, RemoveFromCartForm
from . import cart_service


# ============================================
# UNIT TESTS - Single Model/Class Testing
# ============================================

class BookModelUnitTests(TestCase):
    """Unit tests for Book model - testing single class behavior"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data once for all tests in this class"""
        cls.book = Book.objects.create(
            title="Harry Potter",
            author="JK Rowling",
            price="25.00",
        )

    def test_book_creation(self):
        """Test book is created correctly"""
        self.assertEqual(self.book.title, "Harry Potter")
        self.assertEqual(self.book.author, "JK Rowling")
        self.assertEqual(str(self.book.price), "25.00")

    def test_book_string_representation(self):
        """Test the __str__ method returns book title"""
        self.assertEqual(str(self.book), "Harry Potter")

    def test_book_get_absolute_url(self):
        """Test get_absolute_url returns correct URL"""
        url = self.book.get_absolute_url()
        self.assertEqual(url, reverse("book_detail", args=[str(self.book.id)]))

    def test_book_title_max_length(self):
        """Test book title field max length"""
        max_length = self.book._meta.get_field('title').max_length
        self.assertEqual(max_length, 200)

    def test_book_author_max_length(self):
        """Test book author field max length"""
        max_length = self.book._meta.get_field('author').max_length
        self.assertEqual(max_length, 200)

    def test_book_price_decimal_places(self):
        """Test book price has correct decimal places"""
        decimal_places = self.book._meta.get_field('price').decimal_places
        self.assertEqual(decimal_places, 2)

    def test_book_price_max_digits(self):
        """Test book price has correct max digits"""
        max_digits = self.book._meta.get_field('price').max_digits
        self.assertEqual(max_digits, 6)

    def test_book_uuid_field(self):
        """Test book uses UUID as primary key"""
        self.assertIsNotNone(self.book.id)
        self.assertEqual(len(str(self.book.id)), 36)  # UUID string length

    def test_book_has_special_permission(self):
        """Test book model has special_status permission"""
        permission = Permission.objects.filter(
            codename="special_status",
            content_type__app_label="books"
        ).exists()
        self.assertTrue(permission)


class ReviewModelUnitTests(TestCase):
    """Unit tests for Review model"""
    
    def setUp(self):
        """Set up test data for each test"""
        self.user = get_user_model().objects.create_user(
            username="reviewuser",
            email="review@example.com",
            password="testpass123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            price="15.99",
        )
        self.review = Review.objects.create(
            book=self.book,
            author=self.user,
            review="Great book!"
        )

    def test_review_creation(self):
        """Test review is created correctly"""
        self.assertEqual(self.review.review, "Great book!")
        self.assertEqual(self.review.author, self.user)
        self.assertEqual(self.review.book, self.book)

    def test_review_string_representation(self):
        """Test the __str__ method returns review text"""
        self.assertEqual(str(self.review), "Great book!")

    def test_review_related_name(self):
        """Test review can be accessed via book's related name"""
        reviews = self.book.reviews.all()
        self.assertEqual(reviews.count(), 1)
        self.assertEqual(reviews.first(), self.review)

    def test_review_cascade_delete(self):
        """Test review is deleted when book is deleted"""
        book_id = self.book.id
        review_id = self.review.id
        self.book.delete()
        
        # Book should be deleted
        self.assertFalse(Book.objects.filter(id=book_id).exists())
        # Review should also be deleted due to CASCADE
        self.assertFalse(Review.objects.filter(id=review_id).exists())

    def test_review_max_length(self):
        """Test review field max length"""
        max_length = self.review._meta.get_field('review').max_length
        self.assertEqual(max_length, 255)


class ReviewFormUnitTests(TestCase):
    """Unit tests for ReviewForm"""
    
    def test_form_has_review_field(self):
        """Test form contains review field"""
        form = ReviewForm()
        self.assertIn('review', form.fields)

    def test_form_valid_data(self):
        """Test form is valid with correct data"""
        form_data = {'review': 'This is a great book!'}
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_empty_data(self):
        """Test form is invalid with empty data"""
        form = ReviewForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('review', form.errors)

    def test_form_save_method(self):
        """Test form save method creates review object"""
        user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            price="15.99",
        )
        
        form_data = {'review': 'Amazing read!'}
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        review = form.save(commit=False)
        review.book = book
        review.author = user
        review.save()
        
        self.assertEqual(review.review, 'Amazing read!')
        self.assertEqual(review.book, book)
        self.assertEqual(review.author, user)


class BookListViewUnitTests(TestCase):
    """Unit tests for BookListView"""
    
    def setUp(self):
        """Set up test user and books"""
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.book1 = Book.objects.create(
            title="Book One",
            author="Author One",
            price="10.00",
        )
        self.book2 = Book.objects.create(
            title="Book Two",
            author="Author Two",
            price="20.00",
        )

    def test_book_list_view_requires_login(self):
        """Test book list view requires authentication"""
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_book_list_view_for_logged_in_user(self):
        """Test book list view works for authenticated user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_list.html")

    def test_book_list_view_displays_all_books(self):
        """Test book list view displays all books"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("book_list"))
        self.assertContains(response, "Book One")
        self.assertContains(response, "Book Two")


class BookDetailViewUnitTests(TestCase):
    """Unit tests for BookDetailView"""
    
    def setUp(self):
        """Set up test user, permissions, and book"""
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            price="15.99",
        )

    def test_book_detail_requires_login(self):
        """Test book detail view requires authentication"""
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_book_detail_requires_permission(self):
        """Test book detail view requires special_status permission"""
        self.client.force_login(self.user)
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_book_detail_with_permission(self):
        """Test book detail view works with correct permission"""
        self.user.user_permissions.add(self.special_permission)
        self.client.force_login(self.user)
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_detail.html")

    def test_book_detail_displays_book_info(self):
        """Test book detail view displays book information"""
        self.user.user_permissions.add(self.special_permission)
        self.client.force_login(self.user)
        response = self.client.get(self.book.get_absolute_url())
        self.assertContains(response, "Test Book")
        self.assertContains(response, "Test Author")

    def test_book_detail_invalid_uuid(self):
        """Test book detail view returns 404 for invalid UUID"""
        self.user.user_permissions.add(self.special_permission)
        self.client.force_login(self.user)
        response = self.client.get("/books/12345/")
        self.assertEqual(response.status_code, 404)


class SearchResultsViewUnitTests(TestCase):
    """Unit tests for SearchResultsListView"""
    
    def setUp(self):
        """Set up test books"""
        self.book1 = Book.objects.create(
            title="Django for Beginners",
            author="William Vincent",
            price="39.00",
        )
        self.book2 = Book.objects.create(
            title="Python Crash Course",
            author="Eric Matthes",
            price="35.00",
        )

    def test_search_results_view_loads(self):
        """Test search results view is accessible"""
        response = self.client.get(reverse("search_results") + "?q=Django")#llok for a way to add params to the get request
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,reverse_lazy("search_results"))

    def test_search_by_title(self):
        """Test search finds books by title"""
        response = self.client.get(reverse("search_results") + "?q=Django")
        self.assertContains(response, "Django for Beginners")
        self.assertNotContains(response, "Python Crash Course")

    def test_search_by_author(self):
        """Test search finds books by author"""
        response = self.client.get(reverse("search_results") + "?q=Vincent")
        self.assertContains(response, "Django for Beginners")
        self.assertNotContains(response, "Python Crash Course")

    def test_search_case_insensitive(self):
        """Test search is case insensitive"""
        response = self.client.get(reverse("search_results") + "?q=django")
        self.assertContains(response, "Django for Beginners")


# ============================================
# INTEGRATION TESTS - Multiple Modules
# ============================================

class AuthBookIntegrationTests(TestCase):
    """Integration tests for Auth + Books domain interaction"""
    
    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username="integrationuser",
            email="integration@example.com",
            password="testpass123"
        )
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        self.book = Book.objects.create(
            title="Integration Test Book",
            author="Test Author",
            price="29.99",
        )

    def test_complete_user_book_access_flow(self):
        """Test complete flow: login -> access book list -> access book detail"""
        # Step 1: User attempts to access book list without login
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 302)
        
        # Step 2: User logs in
        self.client.force_login(self.user)
        
        # Step 3: User can now access book list
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Test Book")
        
        # Step 4: User attempts to access book detail without permission
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)
        
        # Step 5: Grant user permission
        self.user.user_permissions.add(self.special_permission)
        
        # Step 6: User can now access book detail
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration Test Book")

    def test_permission_management_flow(self):
        """Test permission granting and revoking affects access"""
        self.client.force_login(self.user)
        
        # Without permission
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)
        
        # Grant permission
        self.user.user_permissions.add(self.special_permission)
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        
        # Revoke permission
        self.user.user_permissions.remove(self.special_permission)
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 403)


class ReviewWorkflowIntegrationTests(TestCase):
    """Integration tests for complete review creation workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="testpass123"
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )
        self.special_permission = Permission.objects.get(
            codename="special_status"
        )
        self.user.user_permissions.add(self.special_permission)
        
        self.book = Book.objects.create(
            title="Reviewable Book",
            author="Book Author",
            price="25.00",
        )

    def test_complete_review_creation_flow(self):
        """Test complete flow: login -> view book -> create review -> see review"""
        # Step 1: Login
        self.client.force_login(self.user)
        
        # Step 2: Access book detail page
        response = self.client.get(self.book.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Submit review
        review_data = {'review': 'This book is fantastic!'}
        response = self.client.post(
            self.book.get_absolute_url(),
            data=review_data,
            follow=True
        )
        
        # Step 4: Verify review was created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Review.objects.filter(
                book=self.book,
                author=self.user,
                review='This book is fantastic!'
            ).exists()
        )
        
        # Step 5: Verify review appears on page
        self.assertContains(response, 'This book is fantastic!')

    def test_multiple_users_reviewing_same_book(self):
        """Test multiple users can review the same book"""
        # Create second user
        user2 = get_user_model().objects.create_user(
            username="reviewer2",
            email="reviewer2@example.com",
            password="testpass123"
        )
        user2.user_permissions.add(self.special_permission)
        
        # First user reviews
        self.client.force_login(self.user)
        self.client.post(
            self.book.get_absolute_url(),
            data={'review': 'Great book by user 1!'}
        )
        self.client.logout()
        
        # Second user reviews
        self.client.force_login(user2)
        self.client.post(
            self.book.get_absolute_url(),
            data={'review': 'Amazing book by user 2!'}
        )
        
        # Both reviews should exist
        self.assertEqual(Review.objects.filter(book=self.book).count(), 2)
        
        # Both reviews should appear on book detail page
        response = self.client.get(self.book.get_absolute_url())
        self.assertContains(response, 'Great book by user 1!')
        self.assertContains(response, 'Amazing book by user 2!')

    def test_review_author_relationship(self):
        """Test review maintains correct relationship with author"""
        self.client.force_login(self.user)
        
        # Create review
        self.client.post(
            self.book.get_absolute_url(),
            data={'review': 'Testing author relationship'}
        )
        
        # Verify review has correct author
        review = Review.objects.get(review='Testing author relationship')
        self.assertEqual(review.author, self.user)
        self.assertEqual(review.author.username, 'reviewer')
        self.assertEqual(review.author.email, 'reviewer@example.com')


class SearchIntegrationTests(TestCase):
    """Integration tests for search functionality across the system"""
    
    def setUp(self):
        """Set up test books with various attributes"""
        self.books = [
            Book.objects.create(
                title="Python Programming",
                author="John Smith",
                price="45.00",
            ),
            Book.objects.create(
                title="Django Web Development",
                author="Jane Doe",
                price="55.00",
            ),
            Book.objects.create(
                title="Advanced Python",
                author="John Smith",
                price="65.00",
            ),
        ]

    def test_search_finds_multiple_results(self):
        """Test search can find multiple matching books"""
        response = self.client.get(reverse("search_results") + "?q=Python")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Programming")
        self.assertContains(response, "Advanced Python")
        self.assertNotContains(response, "Django Web Development")

    def test_search_by_author_finds_multiple_books(self):
        """Test search by author finds all books by that author"""
        response = self.client.get(reverse("search_results") + "?q=John Smith")
        self.assertContains(response, "Python Programming")
        self.assertContains(response, "Advanced Python")
        self.assertNotContains(response, "Django Web Development")

    def test_search_with_no_results(self):
        """Test search handles no results gracefully"""
        response = self.client.get(reverse("search_results") + "?q=NonexistentBook")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Python Programming")
        self.assertNotContains(response, "Django Web Development")

    def test_search_partial_match(self):
        """Test search finds partial matches"""
        response = self.client.get(reverse("search_results") + "?q=Djang")
        self.assertContains(response, "Django Web Development")


# ============================================
# CART TESTS
# ============================================

class CartModelUnitTests(TestCase):
    """Unit tests for Cart and CartItem models."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="cartuser",
            email="cart@example.com",
            password="testpass123",
        )
        self.book = Book.objects.create(
            title="Cart Test Book",
            author="Cart Author",
            price="20.00",
        )

    def test_cart_creation(self):
        """Cart is created with a OneToOne user relationship."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(str(cart), f"Cart of {self.user.username}")

    def test_cart_is_unique_per_user(self):
        """Only one cart per user – second create raises IntegrityError."""
        from django.db import IntegrityError
        Cart.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            Cart.objects.create(user=self.user)

    def test_cartitem_creation(self):
        """CartItem is created and subtotal is computed correctly."""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, book=self.book, quantity=2)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.subtotal, Decimal("40.00"))
        self.assertEqual(str(item), f"2x {self.book.title}")

    def test_unique_cart_book_constraint(self):
        """Cannot add the same book to the same cart twice."""
        from django.db import IntegrityError
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=1)
        with self.assertRaises(IntegrityError):
            CartItem.objects.create(cart=cart, book=self.book, quantity=1)

    def test_cart_total_quantity(self):
        """Cart.total_quantity sums all item quantities."""
        book2 = Book.objects.create(title="B2", author="A", price="10.00")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=3)
        CartItem.objects.create(cart=cart, book=book2, quantity=2)
        self.assertEqual(cart.total_quantity, 5)

    def test_cart_total_price(self):
        """Cart.total returns correct Decimal sum."""
        book2 = Book.objects.create(title="B2", author="A", price="10.00")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=1)  # 20.00
        CartItem.objects.create(cart=cart, book=book2, quantity=3)      # 30.00
        self.assertEqual(cart.total, Decimal("50.00"))

    def test_deleting_cart_cascades_to_items(self):
        """Deleting a cart removes its CartItems."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=1)
        cart_id = cart.id
        cart.delete()
        self.assertFalse(CartItem.objects.filter(cart_id=cart_id).exists())


class CartServiceUserTests(TestCase):
    """Unit tests for cart_service with authenticated users."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="svcuser",
            email="svc@example.com",
            password="testpass123",
        )
        self.book = Book.objects.create(
            title="Service Book",
            author="Author",
            price="15.00",
        )
        self.client.force_login(self.user)

    def test_add_to_cart_creates_item(self):
        response = self.client.post(
            reverse("cart_add"),
            {"book_id": str(self.book.pk), "quantity": 2},
        )
        self.assertRedirects(response, reverse("cart"))
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, book=self.book)
        self.assertEqual(item.quantity, 2)

    def test_add_to_cart_twice_increments_quantity(self):
        """Adding the same book twice increments rather than duplicating."""
        self.client.post(
            reverse("cart_add"),
            {"book_id": str(self.book.pk), "quantity": 1},
        )
        self.client.post(
            reverse("cart_add"),
            {"book_id": str(self.book.pk), "quantity": 3},
        )
        item = CartItem.objects.get(cart__user=self.user, book=self.book)
        self.assertEqual(item.quantity, 4)

    def test_update_cart_item(self):
        self.client.post(
            reverse("cart_add"),
            {"book_id": str(self.book.pk), "quantity": 1},
        )
        self.client.post(
            reverse("cart_update"),
            {"book_id": str(self.book.pk), "quantity": 5},
        )
        item = CartItem.objects.get(cart__user=self.user, book=self.book)
        self.assertEqual(item.quantity, 5)

    def test_remove_from_cart(self):
        self.client.post(
            reverse("cart_add"),
            {"book_id": str(self.book.pk), "quantity": 1},
        )
        self.client.post(
            reverse("cart_remove"),
            {"book_id": str(self.book.pk)},
        )
        self.assertFalse(
            CartItem.objects.filter(cart__user=self.user, book=self.book).exists()
        )

    def test_clear_cart(self):
        book2 = Book.objects.create(title="B2", author="A", price="5.00")
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 1}
        )
        self.client.post(
            reverse("cart_add"), {"book_id": str(book2.pk), "quantity": 2}
        )
        self.client.post(reverse("cart_clear"))
        self.assertEqual(CartItem.objects.filter(cart__user=self.user).count(), 0)

    def test_cart_view_shows_items_and_total(self):
        self.client.post(
            reverse("cart_add"),
            {"book_id": str(self.book.pk), "quantity": 2},
        )
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Service Book")
        self.assertContains(response, "30.00")  # 2 * 15.00

    def test_cart_view_empty_state(self):
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your cart is empty")

    def test_cart_mutation_endpoints_reject_get(self):
        """Add/update/remove/clear endpoints redirect on GET."""
        for url_name in ("cart_add", "cart_update", "cart_remove", "cart_clear"):
            response = self.client.get(reverse(url_name))
            self.assertRedirects(response, reverse("cart"), msg_prefix=url_name)


class CartServiceGuestTests(TestCase):
    """Unit tests for cart_service with anonymous (guest) users."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Guest Book",
            author="Guest Author",
            price="10.00",
        )

    def test_guest_add_to_cart_stored_in_session(self):
        response = self.client.post(
            reverse("cart_add"),
            {"book_id": str(self.book.pk), "quantity": 3},
        )
        self.assertRedirects(response, reverse("cart"))
        session = self.client.session
        self.assertEqual(session["guest_cart"].get(str(self.book.pk)), 3)

    def test_guest_add_twice_increments(self):
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 1}
        )
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 2}
        )
        self.assertEqual(
            self.client.session["guest_cart"].get(str(self.book.pk)), 3
        )

    def test_guest_cart_count_in_context(self):
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 4}
        )
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.context["cart_count"], 4)

    def test_guest_cart_view_shows_items(self):
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 2}
        )
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "Guest Book")
        self.assertContains(response, "20.00")  # 2 * 10.00

    def test_guest_remove_from_cart(self):
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 1}
        )
        self.client.post(
            reverse("cart_remove"), {"book_id": str(self.book.pk)}
        )
        self.assertNotIn(
            str(self.book.pk),
            self.client.session.get("guest_cart", {}),
        )


class CartMergeTests(TestCase):
    """Integration tests for guest-cart merge on login."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="mergeuser",
            email="merge@example.com",
            password="testpass123",
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True,
        )
        self.book = Book.objects.create(
            title="Merge Book",
            author="Author",
            price="25.00",
        )

    def test_session_cart_merged_on_login(self):
        """Guest cart is merged into user cart after login."""
        # Guest adds book
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 2}
        )
        self.assertEqual(
            self.client.session.get("guest_cart", {}).get(str(self.book.pk)), 2
        )

        # Guest logs in via force_login (triggers user_logged_in signal)
        self.client.force_login(self.user)

        # Session cart should be cleared
        self.assertNotIn("guest_cart", self.client.session)

        # User's DB cart should have the item
        self.assertTrue(
            CartItem.objects.filter(
                cart__user=self.user, book=self.book, quantity=2
            ).exists()
        )

    def test_merge_increments_existing_user_cart_item(self):
        """Merging guest cart with existing DB item increments quantity."""
        # Pre-populate user's DB cart
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=1)

        # Guest adds same book (2)
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 2}
        )

        # Login – triggers merge
        self.client.force_login(self.user)

        item = CartItem.objects.get(cart__user=self.user, book=self.book)
        self.assertEqual(item.quantity, 3)

    def test_session_cart_cleared_after_merge(self):
        """Session guest_cart key is removed after merge."""
        self.client.post(
            reverse("cart_add"), {"book_id": str(self.book.pk), "quantity": 1}
        )
        self.client.force_login(self.user)
        self.assertNotIn("guest_cart", self.client.session)


class CartFormUnitTests(TestCase):
    """Unit tests for cart-related forms."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Form Book", author="Author", price="9.99"
        )

    def test_add_to_cart_form_valid(self):
        form = AddToCartForm(
            data={"book_id": str(self.book.pk), "quantity": 2}
        )
        self.assertTrue(form.is_valid())

    def test_add_to_cart_form_invalid_quantity(self):
        form = AddToCartForm(
            data={"book_id": str(self.book.pk), "quantity": 0}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_add_to_cart_form_quantity_too_high(self):
        form = AddToCartForm(
            data={"book_id": str(self.book.pk), "quantity": 100}
        )
        self.assertFalse(form.is_valid())

    def test_remove_from_cart_form_valid(self):
        form = RemoveFromCartForm(data={"book_id": str(self.book.pk)})
        self.assertTrue(form.is_valid())

    def test_update_cart_item_form_valid(self):
        form = UpdateCartItemForm(
            data={"book_id": str(self.book.pk), "quantity": 5}
        )
        self.assertTrue(form.is_valid())
