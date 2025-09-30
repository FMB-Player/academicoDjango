def site_info(request):
    """
    Adds site-wide information and user context to all templates.
    """
    context = {
        'SITE_NAME': 'Sistema Académico',
        'SITE_DESCRIPTION': 'Plataforma de gestión académica',
        'CURRENT_YEAR': 2025,
        'DEBUG': False,
    }
    
    # Add user role information if user is authenticated
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_context = {
            'is_admin': request.user.rol == 'ADMIN',
            'is_docente': request.user.rol == 'DOCENTE',
            'is_alumno': request.user.rol == 'ALUMNO',
            'is_preceptor': request.user.rol == 'PRECEPTOR',
            'user_rol': request.user.rol,
            'user_rol_display': request.user.get_rol_display(),
            'user_full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        }
        context.update(user_context)
    
    return context
