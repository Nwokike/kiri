from django import forms
from .models import Project

class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'github_repo_url', 'demo_url']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none placeholder-zinc-500',
                'placeholder': 'Project Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none placeholder-zinc-500 h-32',
                'placeholder': 'What does your project do?'
            }),
            'github_repo_url': forms.URLInput(attrs={
                'class': 'w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none placeholder-zinc-500',
                'placeholder': 'https://github.com/username/repo'
            }),
            'demo_url': forms.URLInput(attrs={
                'class': 'w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none placeholder-zinc-500',
                'placeholder': 'https://kiri.ng/demo (Optional)'
            }),
        }
