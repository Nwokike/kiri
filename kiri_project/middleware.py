
class SecurityHeadersMiddleware:
    """
    Adds required headers for WebContainer/SharedArrayBuffer support.
    Only applied to the Studio page to avoid breaking external resources (like images) on other pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Cross-Origin Isolation for WASM (Studio only)
        if request.path.startswith('/studio/'):
            response['Cross-Origin-Opener-Policy'] = 'same-origin'
            response['Cross-Origin-Embedder-Policy'] = 'require-corp'
            
        # Standardize CORP globally to allow resources to be embedded/fetched
        # under allow-corp or require-corp policies (critical for Studio AI/Static)
        if 'Cross-Origin-Resource-Policy' not in response:
            response['Cross-Origin-Resource-Policy'] = 'cross-origin'
            
        return response
