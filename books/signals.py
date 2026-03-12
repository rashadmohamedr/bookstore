"""
Books app signals.

Handles merging of the guest (session) cart into the user's database cart
whenever a user logs in via Django's auth_login signal.
"""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .cart_service import merge_session_cart


@receiver(user_logged_in)
def merge_guest_cart_on_login(sender, request, user, **kwargs):
    """Merge any session cart into the user's database cart on login."""
    merge_session_cart(request, user)
