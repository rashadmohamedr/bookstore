
import uuid
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

# Create your models here.
class Book(models.Model):
    id = models.UUIDField(
        primary_key=True,
        db_index=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    cover = models.ImageField(upload_to="covers/",blank=True)
    class Meta: 
        indexes = [
            models.Index( fields=["id"],name="id_index" )
        ]
        permissions = [
        ("special_status", "Can read all books"),
        ]
    def __str__(self) -> str:
        return self.title
    def get_absolute_url(self):
        return reverse("book_detail", args=[str(self.id)])#type: ignore
    
class Review(models.Model): 
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    review = models.CharField(max_length=255)
    author = models.ForeignKey(get_user_model(),on_delete=models.CASCADE,)
    def __str__(self):
        return self.review
    
class Cart(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total(self):
        from decimal import Decimal
        return sum(
            (item.subtotal for item in self.items.select_related("book")),
            Decimal("0.00"),
        )

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "book"], name="unique_cart_book")
        ]

    def __str__(self):
        return f"{self.quantity}x {self.book.title}"

    @property
    def subtotal(self):
        from decimal import Decimal
        price = Decimal(str(self.book.price))
        return price * self.quantity