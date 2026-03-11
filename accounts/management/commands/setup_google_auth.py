import os
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django_project import settings

class Command(BaseCommand):
    help = 'Creates a Google SocialApp based on environment variables'

    def handle(self, *args, **options):
        client_id = settings.GOOGLE_CLIENT_ID 
        secret = settings.GOOGLE_CLIENT_SECRET
        
        if not client_id or not secret:
            self.stdout.write(self.style.WARNING('GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set. Skipping SocialApp creation.'))
            return

        provider = 'google'
        
        # Ensure Site exists (default is usually example.com or localhost)
        # In a real dev env, you might want to force it to localhost:8000
        site = Site.objects.get_current()
        # You can optionally update the site domain here if needed
        # site.domain = 'localhost:8000'
        # site.name = 'Bookstore'
        # site.save()

        try:
            app = SocialApp.objects.get(provider=provider)
            self.stdout.write(self.style.SUCCESS(f'SocialApp "{provider}" already exists. Updating credentials...'))
            app.client_id = client_id
            app.secret = secret
            app.save()
        except SocialApp.DoesNotExist:
            self.stdout.write(self.style.SUCCESS(f'SocialApp "{provider}" not found. Creating...'))
            app = SocialApp.objects.create(
                provider=provider,
                name='Google',
                client_id=client_id,
                secret=secret,
            )
        
        # Ensure the site is associated
        if not app.sites.filter(id=site.id).exists():
            app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f'Added site "{site.domain}" to SocialApp "{provider}".'))
        
        self.stdout.write(self.style.SUCCESS('SocialApp setup complete.'))
