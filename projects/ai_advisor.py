
import logging
from django.conf import settings
from core.ai_service import get_ai_service
from .models import Project, ProjectInsight

logger = logging.getLogger(__name__)

async def analyze_project(project_id: int):
    """
    Analyze a project using AI to generate key insights.
    This runs asynchronously (designed for Huey task).
    """
    try:
        project = await Project.objects.aget(pk=project_id)
        
        # 1. Gather Context
        from projects.services import GitHubService
        # Run sync function in thread since we are in async context
        import asyncio
        from asgiref.sync import sync_to_async
        
        repo_data = await sync_to_async(GitHubService.fetch_structure)(project.github_repo_url)
        
        if not repo_data:
            # Fallback to basic description if fetch fails
            repo_context = "(Failed to fetch deep repository details. Analysis based on metadata.)"
        else:
            repo_context = f"""
            File Structure (Top 150 files): {', '.join(repo_data.get('file_list', []))}
            README Content (first 5k chars):
            {repo_data.get('readme', '')}
            
            Configurations:
            - package.json found: {'Yes' if repo_data.get('package_json') else 'No'}
            - requirements.txt found: {'Yes' if repo_data.get('requirements_txt') else 'No'}
            - Dockerfile found: {'Yes' if repo_data.get('dockerfile') else 'No'}
            
            Main Entry Point Content:
            {repo_data.get('main_file', '(Not found)')}
            """

        context = f"""
        Project Name: {project.name}
        Description: {project.description}
        Category: {project.get_category_display()}
        Primary Language: {project.language}
        Topics: {', '.join(project.topics)}
        GitHub URL: {project.github_repo_url}
        
        Repository Deep Dive:
        {repo_context}
        """
        
        # 2. Construct Prompt
        prompt = f"""
        You are an expert Senior Software Architect. deeply analyze this software project based on its actual file structure and code.
        
        {context}
        
        Provide a structured analysis in JSON format with the following keys:
        1. "summary": A professional 2-3 sentence executive summary of what this project does and its value.
        2. "tech_stack": A list of technologies, frameworks, and tools detected from the file structure/configs.
        3. "complexity_score": An integer from 1-10 (1=Hello World, 10=Linux Kernel).
        4. "complexity_reason": A brief explanation for the score based on code volume/architecture.
        5. "improvements": A list of 3 specific technical suggestions (e.g., "Add Dockerfile", "Use Poetry", "Refactor X").
        6. "roadmap": A list of 3 logical next features to build.
        
        Return ONLY valid JSON.
        """
        
        # 3. Call AI Service
        ai_service = get_ai_service()
        response = await ai_service.generate_json(prompt)
        
        if not response:
            logger.error(f"Failed to generate insight for project {project_id}")
            return None
            
        # 4. Save/Update Insight
        insight, created = await ProjectInsight.objects.aupdate_or_create(
            project=project,
            defaults={
                'summary': response.get('summary', ''),
                'tech_stack': response.get('tech_stack', []),
                'complexity_score': response.get('complexity_score', 5),
                'complexity_reason': response.get('complexity_reason', ''),
                'improvements': response.get('improvements', []),
                'roadmap': response.get('roadmap', []),
                'ai_model_used': settings.AI_MODEL_NAME_GEMINI  # Default or from service
            }
        )
        
        logger.info(f"AI Analysis completed for {project.name}")
        return insight

    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error analyzing project {project_id}: {str(e)}")
        # Log to our new ErrorLog!
        from core.models import ErrorLog
        await ErrorLog.objects.acreate(
            level='error',
            path='projects.ai_advisor.analyze_project',
            message=str(e),
            exception_type=type(e).__name__
        )
        return None
