from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required
from .registry import TOOLS

# Static class map for Tailwind JIT compatibility.
# Dynamic classes like bg-{{ color }}-500/5 are purged by Tailwind v4.
# This maps registry color names to concrete CSS classes.
COLOR_CLASSES = {
    'blue': {
        'bg_accent': 'bg-blue-500/5',
        'bg_icon': 'bg-blue-50 dark:bg-blue-900/20',
        'text_icon': 'text-blue-600 dark:text-blue-400',
    },
    'green': {
        'bg_accent': 'bg-green-500/5',
        'bg_icon': 'bg-green-50 dark:bg-green-900/20',
        'text_icon': 'text-green-600 dark:text-green-400',
    },
    'purple': {
        'bg_accent': 'bg-purple-500/5',
        'bg_icon': 'bg-purple-50 dark:bg-purple-900/20',
        'text_icon': 'text-purple-600 dark:text-purple-400',
    },
    'rose': {
        'bg_accent': 'bg-rose-500/5',
        'bg_icon': 'bg-rose-50 dark:bg-rose-900/20',
        'text_icon': 'text-rose-600 dark:text-rose-400',
    },
    'cyan': {
        'bg_accent': 'bg-cyan-500/5',
        'bg_icon': 'bg-cyan-50 dark:bg-cyan-900/20',
        'text_icon': 'text-cyan-600 dark:text-cyan-400',
    },
    'amber': {
        'bg_accent': 'bg-amber-500/5',
        'bg_icon': 'bg-amber-50 dark:bg-amber-900/20',
        'text_icon': 'text-amber-600 dark:text-amber-400',
    },
    'indigo': {
        'bg_accent': 'bg-indigo-500/5',
        'bg_icon': 'bg-indigo-50 dark:bg-indigo-900/20',
        'text_icon': 'text-indigo-600 dark:text-indigo-400',
    },
    'fuchsia': {
        'bg_accent': 'bg-fuchsia-500/5',
        'bg_icon': 'bg-fuchsia-50 dark:bg-fuchsia-900/20',
        'text_icon': 'text-fuchsia-600 dark:text-fuchsia-400',
    },
    'emerald': {
        'bg_accent': 'bg-emerald-500/5',
        'bg_icon': 'bg-emerald-50 dark:bg-emerald-900/20',
        'text_icon': 'text-emerald-600 dark:text-emerald-400',
    },
    'teal': {
        'bg_accent': 'bg-teal-500/5',
        'bg_icon': 'bg-teal-50 dark:bg-teal-900/20',
        'text_icon': 'text-teal-600 dark:text-teal-400',
    },
    'sky': {
        'bg_accent': 'bg-sky-500/5',
        'bg_icon': 'bg-sky-50 dark:bg-sky-900/20',
        'text_icon': 'text-sky-600 dark:text-sky-400',
    },
    'orange': {
        'bg_accent': 'bg-orange-500/5',
        'bg_icon': 'bg-orange-50 dark:bg-orange-900/20',
        'text_icon': 'text-orange-600 dark:text-orange-400',
    },
    'lime': {
        'bg_accent': 'bg-lime-500/5',
        'bg_icon': 'bg-lime-50 dark:bg-lime-900/20',
        'text_icon': 'text-lime-600 dark:text-lime-400',
    },
    'stone': {
        'bg_accent': 'bg-stone-500/5',
        'bg_icon': 'bg-stone-50 dark:bg-stone-900/20',
        'text_icon': 'text-stone-600 dark:text-stone-400',
    },
    'violet': {
        'bg_accent': 'bg-violet-500/5',
        'bg_icon': 'bg-violet-50 dark:bg-violet-900/20',
        'text_icon': 'text-violet-600 dark:text-violet-400',
    },
    'pink': {
        'bg_accent': 'bg-pink-500/5',
        'bg_icon': 'bg-pink-50 dark:bg-pink-900/20',
        'text_icon': 'text-pink-600 dark:text-pink-400',
    },
    'yellow': {
        'bg_accent': 'bg-yellow-500/5',
        'bg_icon': 'bg-yellow-50 dark:bg-yellow-900/20',
        'text_icon': 'text-yellow-600 dark:text-yellow-400',
    },
    'slate': {
        'bg_accent': 'bg-slate-500/5',
        'bg_icon': 'bg-slate-50 dark:bg-slate-900/20',
        'text_icon': 'text-slate-600 dark:text-slate-400',
    },
}

DEFAULT_COLOR = {
    'bg_accent': 'bg-gray-500/5',
    'bg_icon': 'bg-gray-50 dark:bg-gray-900/20',
    'text_icon': 'text-gray-600 dark:text-gray-400',
}


@login_not_required
def index(request):
    """Tools Hub - displays all available tools grouped by category."""
    categories = {}
    tool_count = 0
    for slug, tool in TOOLS.items():
        cat = tool['category']
        if cat not in categories:
            categories[cat] = []
        tool_with_slug = tool.copy()
        tool_with_slug['slug'] = slug
        tool_with_slug['color_classes'] = COLOR_CLASSES.get(tool.get('color', ''), DEFAULT_COLOR)
        categories[cat].append(tool_with_slug)
        tool_count += 1

    return render(request, 'tools/index.html', {
        'categories': categories,
        'tool_count': tool_count,
    })


@login_not_required
def tool_detail(request, tool_slug):
    """Generic tool view that renders the tool-specific template."""
    tool = TOOLS.get(tool_slug)
    if not tool:
        from django.http import Http404
        raise Http404("Tool not found")

    return render(request, f"tools/{tool['template']}.html", {'tool': tool})
