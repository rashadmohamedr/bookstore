from django.urls import path, include
from .views import (
    BookListView,
    BookDetailView,
    SearchResultsListView,
    CartView,
    AddToCartView,
    UpdateCartItemView,
    RemoveFromCartView,
    ClearCartView,
)

urlpatterns = [
    path("", BookListView.as_view(), name="book_list"),
    path("<uuid:pk>/", BookDetailView.as_view(), name="book_detail"),
    path("search/", SearchResultsListView.as_view(), name="search_results"),
    # Cart
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", AddToCartView.as_view(), name="cart_add"),
    path("cart/update/", UpdateCartItemView.as_view(), name="cart_update"),
    path("cart/remove/", RemoveFromCartView.as_view(), name="cart_remove"),
    path("cart/clear/", ClearCartView.as_view(), name="cart_clear"),
]