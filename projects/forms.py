import json
from django import forms
from .models import Project


class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'category',
            'github_repo_url',
            'demo_url',
            'huggingface_url',
            'language',
            'topics',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe the project in a few sentences...',
            }),
            'topics': forms.TextInput(attrs={
                'placeholder': 'e.g. nlp, transformer, edge-ai',
            }),
        }
        help_texts = {
            'github_repo_url': 'Full GitHub repository URL (e.g. https://github.com/user/repo)',
            'topics': 'Comma-separated tags. Auto-synced from GitHub if left empty.',
            'demo_url': 'Optional live demo or paper URL.',
            'huggingface_url': 'Optional Hugging Face model/dataset URL.',
        }

    def clean_topics(self):
        data = self.cleaned_data.get('topics', '')
        if not data:
            return []
        # Handle pre-filled JSON array strings (e.g. from import flow)
        if isinstance(data, list):
            topics = data
        else:
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    topics = parsed
                else:
                    topics = [str(parsed)]
            except (json.JSONDecodeError, ValueError):
                topics = [t.strip() for t in data.split(',') if t.strip()]
        # Enforce limits
        topics = [str(t)[:50] for t in topics[:20]]
        return topics
