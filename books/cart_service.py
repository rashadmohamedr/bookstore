"""
Cart service: centralised logic for loading, adding, updating, removing and
merging cart items.  Supports both authenticated users (database-backed) and
guests (session-backed).

Session cart format:
    request.session["guest_cart"] = {"<str(book_id)>": <int quantity>, ...}
"""

from decimal import Decimal

from .models import Book, Cart, CartItem

SESSION_CART_KEY = "guest_cart"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session_cart(request) -> dict:
    """Return the raw session-cart dict, creating it when absent."""
    cart = request.session.get(SESSION_CART_KEY)
    if not isinstance(cart, dict):
        cart = {}
        request.session[SESSION_CART_KEY] = cart
    return cart


def _save_session_cart(request, cart: dict) -> None:
    request.session[SESSION_CART_KEY] = cart
    request.session.modified = True


def _get_or_create_user_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_to_cart(request, book_id: str, quantity: int = 1) -> None:
    """Add *quantity* of *book_id* to the cart (guest or user)."""
    quantity = max(1, int(quantity))
    if request.user.is_authenticated:
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return
        cart = _get_or_create_user_cart(request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, book=book)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
    else:
        session_cart = _get_session_cart(request)
        key = str(book_id)
        session_cart[key] = session_cart.get(key, 0) + quantity
        _save_session_cart(request, session_cart)


def update_cart_item(request, book_id: str, quantity: int) -> None:
    """Set the quantity for *book_id*.  Removes the item if quantity <= 0."""
    quantity = int(quantity)
    if quantity <= 0:
        remove_from_cart(request, book_id)
        return
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(cart=cart, book_id=book_id)
            item.quantity = quantity
            item.save()
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            pass
    else:
        session_cart = _get_session_cart(request)
        key = str(book_id)
        if key in session_cart:
            session_cart[key] = quantity
            _save_session_cart(request, session_cart)


def remove_from_cart(request, book_id: str) -> None:
    """Remove *book_id* from the cart entirely."""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.filter(cart=cart, book_id=book_id).delete()
        except Cart.DoesNotExist:
            pass
    else:
        session_cart = _get_session_cart(request)
        session_cart.pop(str(book_id), None)
        _save_session_cart(request, session_cart)


def clear_cart(request) -> None:
    """Remove all items from the cart."""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
    else:
        _save_session_cart(request, {})


def get_cart_items(request) -> list:
    """
    Return a list of dicts representing cart items, suitable for templates.
    Each dict has: book, quantity, subtotal.
    """
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return [
                {
                    "book": item.book,
                    "quantity": item.quantity,
                    "subtotal": item.subtotal,
                }
                for item in cart.items.select_related("book")
            ]
        except Cart.DoesNotExist:
            return []
    else:
        session_cart = _get_session_cart(request)
        if not session_cart:
            return []
        books = {
            str(b.pk): b
            for b in Book.objects.filter(pk__in=session_cart.keys())
        }
        items = []
        for book_id, qty in session_cart.items():
            book = books.get(book_id)
            if book:
                items.append(
                    {
                        "book": book,
                        "quantity": qty,
                        "subtotal": Decimal(str(book.price)) * qty,
                    }
                )
        return items


def get_cart_count(request) -> int:
    """Return total number of items (sum of quantities) in the cart."""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return cart.total_quantity
        except Cart.DoesNotExist:
            return 0
    else:
        return sum(_get_session_cart(request).values())


def get_cart_total(request) -> Decimal:
    """Return the grand total (Decimal) of the cart."""
    return sum(
        (item["subtotal"] for item in get_cart_items(request)),
        Decimal("0.00"),
    )


def merge_session_cart(request, user) -> None:
    """
    Merge the guest session cart into the user's database cart, then clear the
    session cart.  Call this after a user logs in.
    """
    session_cart = request.session.get(SESSION_CART_KEY, {})
    if not session_cart:
        return
    cart = _get_or_create_user_cart(user)
    books = {
        str(b.pk): b
        for b in Book.objects.filter(pk__in=session_cart.keys())
    }
    for book_id, qty in session_cart.items():
        book = books.get(book_id)
        if not book:
            continue
        item, created = CartItem.objects.get_or_create(cart=cart, book=book)
        if not created:
            item.quantity += qty
        else:
            item.quantity = qty
        item.save()
    # Clear session cart after successful merge
    request.session.pop(SESSION_CART_KEY, None)
    request.session.modified = True
