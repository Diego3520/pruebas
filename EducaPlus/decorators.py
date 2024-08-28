from functools import wraps, WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES

from django.shortcuts import redirect


def group_required(*group_names, redirect_route='index'):
    """Requires user membership in at least one of the groups passed in."""

    def decorator(view_func):
        @wraps(view_func, assigned=WRAPPER_ASSIGNMENTS, updated=WRAPPER_UPDATES)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            else:
                return redirect(redirect_route)

        return _wrapped_view

    return decorator
