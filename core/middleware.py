from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve
from django.http import HttpResponseForbidden

class RestrictedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(settings.STATIC_URL):
            return self.get_response(request)
        if settings.MEDIA_URL and request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        if request.user.is_authenticated and request.user.username == "centrale_operativa":
            allowed_url_names = [
                'documenti',
                'login',
                'logout',
            ]
            
            try:
                current_url_name = resolve(request.path_info).url_name
            except:
                current_url_name = None

            if current_url_name not in allowed_url_names:
                return redirect('documenti')

        response = self.get_response(request)
        return response