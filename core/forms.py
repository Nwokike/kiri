from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Add to the discussion...',
                'class': 'w-full p-3 rounded-lg border border-border bg-bg-primary text-text-primary focus:border-accent focus:ring-1 focus:ring-accent dark:bg-dark-surface dark:border-dark-border dark:text-dark-text dark:placeholder-dark-secondary'
            }),
        }
