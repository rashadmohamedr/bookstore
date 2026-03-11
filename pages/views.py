from django.views.generic import TemplateView
from accounts.models import CustomUser

# Create your views here.
class HomePageView(TemplateView):
    template_name = "home.html"
    model = CustomUser
    
    
class AboutPageView(TemplateView):
    template_name = "about.html"