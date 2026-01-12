from django import forms
from .models import Project
from turnstile.fields import TurnstileField

class ProjectSubmissionForm(forms.ModelForm):
    turnstile = TurnstileField(theme='auto')

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
            'topics'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full p-3 rounded-lg border border-border bg-bg-primary text-text-primary focus:border-brand-green focus:ring-1 focus:ring-brand-green dark:bg-dark-surface dark:border-dark-border dark:text-dark-text'
            }),
            'topics': forms.TextInput(attrs={
                'placeholder': 'e.g. transformers, cv, nlp (comma separated)',
                'class': 'w-full p-3 rounded-lg border border-border bg-bg-primary text-text-primary focus:border-brand-green focus:ring-1 focus:ring-brand-green dark:bg-dark-surface dark:border-dark-border dark:text-dark-text'
            }),
            'language': forms.TextInput(attrs={
                'placeholder': 'e.g. Python, JavaScript',
                'class': 'w-full p-3 rounded-lg border border-border bg-bg-primary text-text-primary focus:border-brand-green focus:ring-1 focus:ring-brand-green dark:bg-dark-surface dark:border-dark-border dark:text-dark-text'
            }),
        }
        help_texts = {
            'github_repo_url': 'Public GitHub repository URL (required for stats sync).',
            'topics': 'Tags will be auto-synced from GitHub if left empty.',
        }

    def clean_topics(self):
        # Convert comma separated string to list if entered manually
        data = self.cleaned_data['topics']
        if isinstance(data, str):
            # Split by comma, strip whitespace, filtering empty strings
            return [t.strip() for t in data.split(',') if t.strip()]
        return data
