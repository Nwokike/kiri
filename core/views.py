from django.shortcuts import render


def home(request):
    """Landing page - The Manifesto Site."""
    projects = [
        {
            "name": "Imara",
            "description": "Digital Bodyguard protecting women and girls from online gender-based violence in messaging apps.",
            "url": "https://imara.africa",
            "github": "https://github.com/Nwokike/Imara",
            "color": "#800080",
        },
        {
            "name": "SpanInsight",
            "description": "Data intelligence platform for businesses and researchers to collect forms, analyze data, and build dashboards.",
            "url": "https://spaninsight.com/",
            "github": "https://github.com/Nwokike/spaninsight",
            "color": "#0066CC",
        },
        {
            "name": "Igbo Archives",
            "description": "Modern PWA preserving Igbo cultural heritage with Django, HTMX, and AI-powered insights.",
            "url": "https://igboarchives.com.ng",
            "github": "https://github.com/Nwokike/igbo-archives-platform",
            "color": "#8B4513",
        },
        {
            "name": "Kiriong",
            "description": "Django platform empowering Nigerian artisans with marketplace, AI learning academy, and community tools.",
            "url": "https://kiriong.onrender.com",
            "github": "https://github.com/Nwokike/kiriong",
            "color": "#006400",
        },
        {
            "name": "Akili",
            "description": "Learning platform with courses, quizzes, KaTeX for math formulas, and full PWA support.",
            "url": "https://akili-jwe7.onrender.com",
            "github": "https://github.com/Nwokike/Akili",
            "color": "#4B0082",
        },
        {
            "name": "YieldWise AI",
            "description": "AI platform for African farmers providing farm planning, crop disease diagnosis, and business insights.",
            "url": "https://yieldwise-ai.onrender.com/",
            "github": "https://github.com/Nwokike/yieldwise-ai",
            "color": "#228B22",
        },
    ]
    
    research_areas = [
        {"name": "Natural Language Processing", "icon": "fas fa-language", "description": "Building language models for African languages including Igbo, Yoruba, and Pidgin."},
        {"name": "AI Safety & Ethics", "icon": "fas fa-shield-alt", "description": "Developing guardrails and safety mechanisms for AI systems in African contexts."},
        {"name": "Edge Computing", "icon": "fas fa-microchip", "description": "Optimizing AI models to run on low-resource devices and unstable networks."},
        {"name": "Agricultural AI", "icon": "fas fa-seedling", "description": "Machine learning applications for crop monitoring, disease detection, and yield prediction."},
    ]
    
    return render(request, "home.html", {
        "projects": projects,
        "research_areas": research_areas,
    })


def about(request):
    """About Kiri Research Labs page."""
    return render(request, "about.html")


def research(request):
    """Research papers and publications."""
    papers = [
        {
            "title": "Sovereign AI: Running Llama-3 on Tecno Devices",
            "abstract": "Exploring techniques for deploying large language models on affordable African smartphones using quantization and edge optimization.",
            "status": "In Progress",
        },
        {
            "title": "The Green Metric: Benchmarking Edge vs. Cloud Energy",
            "abstract": "Measuring the environmental impact of AI inference on edge devices compared to traditional cloud data centers.",
            "status": "Draft",
        },
        {
            "title": "Imara Protocol: Offline Safety for Rural Communities",
            "abstract": "A framework for protecting vulnerable users from online harm in areas with intermittent internet connectivity.",
            "status": "Published",
        },
    ]
    return render(request, "research.html", {"papers": papers})
