from django.test import TestCase
from django.urls import reverse
from .registry import TOOLS

class ToolsViewTests(TestCase):
    """Ensure all tool pages render successfully."""
    
    def test_index_renders(self):
        """Test the tools hub index page."""
        url = reverse('tools:index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_all_registry_tools_render(self):
        """
        Iterate through all tools in the registry and verify
        that their detail pages render successfully.
        """
        for slug in TOOLS.keys():
            url = reverse('tools:tool_detail', kwargs={'tool_slug': slug})
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, 
                f"Tool page for '{slug}' (template: {TOOLS[slug]['template']}) failed to render"
            )
