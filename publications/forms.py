from django import forms
from .models import Publication

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['title', 'abstract', 'github_repo_url', 'github_file_path', 'executable_script', 'arxiv_id', 'doi', 'is_published']
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 3, 'class': 'w-full bg-[#1E1E1E] border border-[#333] rounded p-2 text-[#CCCCCC]'}),
            'executable_script': forms.Textarea(attrs={'rows': 5, 'class': 'font-mono text-xs'}),
        }
        help_texts = {
            'github_repo_url': 'URL to your GitHub repository (e.g., https://github.com/username/repo)',
            'github_file_path': 'Path to the markdown file inside the repo (e.g., papers/intro.md)',
        }

    def clean(self):
        cleaned_data = super().clean()
        repo_url = cleaned_data.get('github_repo_url')
        file_path = cleaned_data.get('github_file_path')
        
        if repo_url and not file_path:
            self.add_error('github_file_path', 'File path is required when providing a GitHub URL.')
            
        return cleaned_data
