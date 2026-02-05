from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin #look at the class implementation in the src
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import ListView, DetailView
from .models import Book

# Create your views here.
class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name="books/book_list.html"
    login_url="account_login"
    
class BookDetailView(LoginRequiredMixin,PermissionRequiredMixin, DetailView):
    model = Book
    template_name = "books/book_detail.html"
    login_url="account_login"
    permission_required="books.special_status"
    
class SearchResultsListView(ListView):
    model = Book
    template_name = "books/search_results.html"
    def get_queryset(self):
        query = self.request.GET.get("q")
        return Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        )
    