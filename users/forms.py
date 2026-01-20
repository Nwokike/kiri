from allauth.account.forms import LoginForm
from turnstile.fields import TurnstileField

class CustomLoginForm(LoginForm):
    turnstile = TurnstileField()

from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    turnstile = TurnstileField()
