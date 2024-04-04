from django.shortcuts import redirect


def check_user_authentication(get_response):
    def middleware(request):
        print("Checking user authentication...")
        if not 'uid' in request.session and request.path not in ['/login/','/index/']:
            print("User is not authenticated. Redirecting to login page...")
            return redirect('/login/')
        response = get_response(request)
        return response

    return middleware
