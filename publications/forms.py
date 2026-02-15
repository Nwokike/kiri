from django import forms
from .models import Publication
from core.forms import TEXTAREA_CLASS, INPUT_CLASS

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['title', 'abstract', 'content', 'github_repo_url', 'github_file_path', 'executable_script', 'arxiv_id', 'doi', 'is_published']
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 3, 'class': TEXTAREA_CLASS}),
            'content': forms.Textarea(attrs={'rows': 10, 'class': TEXTAREA_CLASS}),
            'github_repo_url': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'github_file_path': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'executable_script': forms.Textarea(attrs={'rows': 5, 'class': 'font-mono text-xs ' + TEXTAREA_CLASS}),
            'arxiv_id': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'doi': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }
        help_texts = {
            'content': 'Main content in Markdown. This acts as a fallback or static version if GitHub content is not provided.',
            'github_repo_url': 'URL to your GitHub repository (e.g., https://github.com/username/repo)',
            'github_file_path': 'Path to the markdown file inside the repo (e.g., papers/intro.md)',
        }

    def clean(self):
        cleaned_data = super().clean()
        repo_url = cleaned_data.get('github_repo_url')
        file_path = cleaned_data.get('github_file_path')
        
        if repo_url and not file_path:
            self.add_error('github_file_path', 'File path is required when providing a GitHub URL.')
        if file_path and not repo_url:
            self.add_error('github_repo_url', 'Repository URL is required when providing a file path.')
            
        return cleaned_data
