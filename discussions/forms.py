from django import forms
from .models import Topic, Reply

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'category', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'w-full'}),
            'title': forms.TextInput(attrs={'class': 'w-full'}),
            'category': forms.Select(attrs={'class': 'w-full'}),
        }

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'w-full', 'placeholder': 'Write a reply...'}),
        }
