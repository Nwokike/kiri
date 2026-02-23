from django import forms
from turnstile.fields import TurnstileField
from .models import Comment

# Shared Tailwind CSS classes for forms
# Shared Tailwind classes for consistent styling
TEXTAREA_CLASS = 'w-full p-3 rounded-lg border border-[#E4E4E7] bg-white text-[#18181B] focus:border-[#10B981] focus:ring-1 focus:ring-[#10B981] dark:bg-[#1E1E1E] dark:border-[#333] dark:text-[#E4E4E7] dark:placeholder-[#6C757D]'
INPUT_CLASS = 'w-full p-3 rounded-lg border border-[#E4E4E7] bg-white text-[#18181B] focus:border-[#10B981] focus:ring-1 focus:ring-[#10B981] dark:bg-[#1E1E1E] dark:border-[#333] dark:text-[#E4E4E7] dark:placeholder-[#6C757D]'

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
