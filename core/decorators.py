from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import Usuario

def role_required(*roles):
    """
    Decorator for views that checks that the user has one of the specified roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Por favor inicia sesión para acceder a esta página.')
                return redirect(f"{reverse('login')}?next={request.path}")
                
            if request.user.rol not in roles:
                messages.error(request, 'No tienes permiso para acceder a esta página.')
                return redirect('home')
                
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
