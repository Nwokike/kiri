from django import forms
from turnstile.fields import TurnstileField
from .models import Comment

# Shared Tailwind CSS classes for forms
TEXTAREA_CLASS = 'w-full p-3 rounded-lg border border-border bg-bg-primary text-text-primary focus:border-accent focus:ring-1 focus:ring-accent dark:bg-dark-surface dark:border-dark-border dark:text-dark-text dark:placeholder-dark-secondary'
INPUT_CLASS = 'w-full p-3 rounded-lg border border-border bg-bg-primary text-text-primary focus:border-accent focus:ring-1 focus:ring-accent dark:bg-dark-surface dark:border-dark-border dark:text-dark-text dark:placeholder-dark-secondary'

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Add to the discussion...',
                'class': TEXTAREA_CLASS
            }),
        }


class ContactForm(forms.Form):
    """Contact form with Turnstile anti-spam protection."""
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)
    turnstile = TurnstileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['name', 'email', 'subject', 'message']:
            self.fields[field].widget.attrs.update({'class': INPUT_CLASS})
