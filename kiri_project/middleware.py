
class SecurityHeadersMiddleware:
    """
    Adds required headers for WebContainer/SharedArrayBuffer support.
    Only applied to the Studio page to avoid breaking external resources (like images) on other pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only apply strict isolation to the Studio
        if request.path.startswith('/studio/'):
            response['Cross-Origin-Opener-Policy'] = 'same-origin'
            response['Cross-Origin-Embedder-Policy'] = 'require-corp'
            
        return response
