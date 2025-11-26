from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from .models import Usuario

def role_required(*roles):
    """
    Decorator for views that checks that the user has one of the specified roles.
    Returns 403 if user doesn't have the required role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Por favor inicia sesión para acceder a esta página.')
                return redirect(f"{reverse('core:login')}?next={request.path}")
                
            if request.user.rol not in roles:
                # Log the unauthorized access attempt (optional)
                print(f"Unauthorized access attempt by user {request.user} to {request.path}")
                
                # Return a 403 response with the error template
                response = render_to_string('core/errors/403.html', {
                    'message': 'No tienes permiso para acceder a esta página.',
                    'status_code': 403
                }, request=request)
                return HttpResponseForbidden(response)
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """Shortcut for admin role required."""
    return role_required(Usuario.Rol.ADMIN)(view_func)

def docente_required(view_func):
    """Shortcut for docente role required."""
    return role_required(Usuario.Rol.DOCENTE)(view_func)

def alumno_required(view_func):
    """Shortcut for alumno role required."""
    return role_required(Usuario.Rol.ALUMNO)(view_func)

def preceptor_required(view_func):
    """Shortcut for preceptor role required."""
    return role_required(Usuario.Rol.PRECEPTOR)(view_func)
