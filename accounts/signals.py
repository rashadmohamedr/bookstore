from django.dispatch import receiver
from allauth.account.signals import user_signed_up

@receiver(user_signed_up)
def handle_user_signed_up(request, user, sociallogin=None, **kwargs):
    """
    Handle user signup for both regular and social logins.
    """
    # Check if this is a social login
    if sociallogin is not None:
        # grab the user's data from social login
        new_user_data = sociallogin.account.extra_data
        print(new_user_data)
        # perform tasks/processing on social login data
    else:
        # Handle regular email/password signup
        print(f"Regular signup for user: {user.username}")
        # perform tasks/processing for regular signup

