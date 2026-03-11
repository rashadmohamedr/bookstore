"""
Project-level template context processors.
"""

from books.cart_service import get_cart_count


def cart(request):
    """Inject ``cart_count`` into every template context."""
    return {"cart_count": get_cart_count(request)}
