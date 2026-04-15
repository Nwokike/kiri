import re
import markdown

def process_markdown(owner, repo_name, raw_markdown):
    """
    Transforms raw GitHub markdown into safe, premium HTML.
    Rewrites relative image and document links to absolute GitHub URLs.
    """
    
    # 1. Rewrite relative image links
    # Matches ![alt](path) where path does not start with http or data:
    image_regex = r'!\[([^\]]*)\]\((?!http|data:)(.*?)\)'
    image_repl = rf'![\1](https://raw.githubusercontent.com/{owner}/{repo_name}/main/\2)'
    markdown_text = re.sub(image_regex, image_repl, raw_markdown)
    
    # 2. Rewrite relative document links
    # Matches [text](path) where path does not start with http, mailto:, or #
    link_regex = r'\[([^\]]+)\]\((?!http|mailto:|#)(.*?)\)'
    link_repl = rf'[\1](https://github.com/{owner}/{repo_name}/blob/main/\2)'
    markdown_text = re.sub(link_regex, link_repl, markdown_text)
    
    # Clean up any double slashes that might have been inadvertently created
    # e.g., if the relative path started with a slash: /docs/setup.md
    markdown_text = markdown_text.replace(f"main//", "main/")
    
    # 3. Compilation
    html_content = markdown.markdown(
        markdown_text,
        extensions=['fenced_code', 'codehilite', 'tables', 'toc']
    )
    
    return html_content
