from django import forms
from .models import Topic, Reply
import nh3
from core.forms import TEXTAREA_CLASS, INPUT_CLASS

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'category', 'project', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': TEXTAREA_CLASS, 'placeholder': 'Start the discussion...'}),
            'title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Discussion Title'}),
            'category': forms.Select(attrs={'class': INPUT_CLASS}),
            'project': forms.Select(attrs={'class': INPUT_CLASS}),
        }
        help_texts = {
            'project': 'Optional: Link this discussion to a specific project.',
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        # 4.1: Sanitize content before saving (simple HTML tags allow list)
        allowed_tags = ['p', 'b', 'i', 'strong', 'em', 'code', 'pre', 'br', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'blockquote']
        allowed_attrs = {'a': ['href', 'title']}
        return nh3.clean(content, tags=set(allowed_tags), attributes=allowed_attrs)

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': TEXTAREA_CLASS, 'placeholder': 'Write a reply...'}),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        allowed_tags = ['p', 'b', 'i', 'strong', 'em', 'code', 'pre', 'br', 'ul', 'ol', 'li', 'a', 'blockquote']
        allowed_attrs = {'a': ['href', 'title']}
        return nh3.clean(content, tags=set(allowed_tags), attributes=allowed_attrs)
