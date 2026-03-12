from typing import Any
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.views.generic import ListView, DetailView, TemplateView, View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Book
from .forms import ReviewForm, AddToCartForm, UpdateCartItemForm, RemoveFromCartForm
from . import cart_service

# Create your views here.
class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name="books/book_list.html"
    login_url="account_login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["add_to_cart_form"] = AddToCartForm()
        return context

@method_decorator(never_cache, name='dispatch')
class BookDetailView(LoginRequiredMixin,PermissionRequiredMixin, DetailView):
    model = Book
    template_name = "books/book_detail.html"
    login_url="account_login"
    permission_required="books.special_status"
    queryset = Book.objects.all().prefetch_related('reviews__author',)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ReviewForm()
        context["add_to_cart_form"] = AddToCartForm(
            initial={"book_id": self.object.pk, "quantity": 1}
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.book = self.object
            review.author = request.user
            review.save()
            return redirect("book_detail", pk=self.object.pk)

        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)
    
class SearchResultsListView(ListView):
    model = Book
    template_name = "books/search_results.html"
    def get_queryset(self):
        query = self.request.GET.get("q")
        return Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["add_to_cart_form"] = AddToCartForm()
        return context


# ---------------------------------------------------------------------------
# Cart views
# ---------------------------------------------------------------------------

class CartView(TemplateView):
    template_name = "books/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = cart_service.get_cart_items(self.request)
        # Attach update/remove forms to each item
        for item in items:
            item["update_form"] = UpdateCartItemForm(
                initial={"book_id": item["book"].pk, "quantity": item["quantity"]}
            )
            item["remove_form"] = RemoveFromCartForm(
                initial={"book_id": item["book"].pk}
            )
        context["cart_items"] = items
        context["cart_total"] = cart_service.get_cart_total(self.request)
        return context


class AddToCartView(View):
    """POST only – add a book to the cart."""

    def post(self, request, *args, **kwargs):
        form = AddToCartForm(request.POST)
        if form.is_valid():
            cart_service.add_to_cart(
                request,
                str(form.cleaned_data["book_id"]),
                form.cleaned_data["quantity"],
            )
        next_url = request.POST.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)
        return redirect("cart")

    def get(self, request, *args, **kwargs):
        return redirect("cart")


class UpdateCartItemView(View):
    """POST only – update quantity for a cart item."""

    def post(self, request, *args, **kwargs):
        form = UpdateCartItemForm(request.POST)
        if form.is_valid():
            cart_service.update_cart_item(
                request,
                str(form.cleaned_data["book_id"]),
                form.cleaned_data["quantity"],
            )
        return redirect("cart")

    def get(self, request, *args, **kwargs):
        return redirect("cart")


class RemoveFromCartView(View):
    """POST only – remove a book from the cart."""

    def post(self, request, *args, **kwargs):
        form = RemoveFromCartForm(request.POST)
        if form.is_valid():
            cart_service.remove_from_cart(
                request,
                str(form.cleaned_data["book_id"]),
            )
        return redirect("cart")

    def get(self, request, *args, **kwargs):
        return redirect("cart")


class ClearCartView(View):
    """POST only – empty the entire cart."""

    def post(self, request, *args, **kwargs):
        cart_service.clear_cart(request)
        return redirect("cart")

    def get(self, request, *args, **kwargs):
        return redirect("cart")
    