from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin #look at the class implementation in the src
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
    