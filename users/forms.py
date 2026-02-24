from allauth.account.forms import LoginForm, SignupForm


class CustomLoginForm(LoginForm):
    """Extended login form. Turnstile removed — rate limiting handled by allauth."""
    pass


class CustomSignupForm(SignupForm):
    """Extended signup form. Turnstile removed — rate limiting handled by allauth."""
    pass
