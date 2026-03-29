from django import forms
from .models import Project


class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'category',
            'status',
            'github_repo_url',
            'huggingface_url',
            'live_url',
            'staging_url',
            'custom_image_url',
            'language',
            'topics',
            'tech_stack',
            'seo_title',
            'seo_description',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Describe the project — ideally as a case study: problem, solution, tech stack, outcome.',
            }),
            'topics': forms.TextInput(attrs={
                'placeholder': 'e.g. nlp, transformer, edge-ai',
            }),
            'tech_stack': forms.TextInput(attrs={
                'placeholder': 'e.g. Django, TinyML, Groq',
            }),
            'seo_title': forms.TextInput(attrs={
                'placeholder': 'Custom page title for search engines (max 70 chars)',
            }),
            'seo_description': forms.TextInput(attrs={
                'placeholder': 'Meta description for search engines (max 160 chars)',
            }),
        }
        help_texts = {
            'github_repo_url': 'Full GitHub repository URL (e.g. https://github.com/user/repo)',
            'huggingface_url': 'Hugging Face Space, Model, or Dataset URL.',
            'topics': 'Comma-separated tags. Auto-synced from GitHub if left empty.',
            'live_url': 'Production URL for live platforms (e.g. https://*.kiri.ng)',
            'staging_url': 'Staging/beta URL for non-live projects.',
            'custom_image_url': 'Override the auto-generated GitHub preview image.',
            'tech_stack': 'Curated technology badges shown on the project card.',
        }
