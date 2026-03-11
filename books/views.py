from typing import Any
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin #look at the class implementation in the src
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import ListView, DetailView
from .models import Book
from .forms import ReviewForm

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
    queryset = Book.objects.all().prefetch_related('reviews__author',)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ReviewForm()
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
    