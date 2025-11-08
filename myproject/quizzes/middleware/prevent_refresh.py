class PreventRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method == 'POST' and 'quiz' in request.path:
            response['Cache-Control'] = 'no-store, must-revalidate'
        return response