from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .decorators import admin_required, docente_required, alumno_required, preceptor_required
from .forms import ProfileEditForm


def home(request):
    """
    Home page view that shows different content based on authentication status.
    """
    return render(request, 'core/home.html')


def login_view(request):
    """
    Handle user login.
    """
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # Using email as username
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_full_name() or user.email}!')
                next_url = request.GET.get('next', 'core:home')
                return redirect(next_url)
        messages.error(request, 'Email o contraseña inválidos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/auth/login.html', {'form': form})


def logout_view(request):
    """
    Handle user logout.
    """
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('core:home')


@login_required
def profile(request):
    """
    User profile page.
    """
    return render(request, 'core/profile.html')


@login_required
def edit_profile(request):
    """
    Edit user profile.
    """
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('core:perfil')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'core/edit_profile.html', {'form': form})


def handler404(request, exception=None, template_name='core/errors/404.html'):
    """
    Custom 404 error handler.
    """
    context = {
        'request_path': request.path,
        'exception': str(exception) if exception else 'Página no encontrada',
    }
    return render(request, template_name, context, status=404)


def handler403(request, exception=None, template_name='core/errors/403.html'):
    """
    Custom 403 error handler.
    """
    context = {
        'exception': str(exception) if exception else 'Acceso denegado',
    }
    return render(request, template_name, context, status=403)


def handler500(request, template_name='core/errors/500.html'):
    """
    Custom 500 error handler.
    """
    context = {
        'request_path': request.path,
        'exception': 'Error interno del servidor',
    }
    return render(request, template_name, context, status=500)


# Dashboard Views
@login_required
def dashboard(request):
    """Main dashboard view that redirects to role-specific dashboards."""
    if request.user.rol == 'ADMIN':
        return redirect('admin_dashboard')
    elif request.user.rol == 'DOCENTE':
        return redirect('docente_dashboard')
    elif request.user.rol == 'ALUMNO':
        return redirect('alumno_dashboard')
    elif request.user.rol == 'PRECEPTOR':
        return redirect('preceptor_dashboard')
    return redirect('core:home')


@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard view."""
    return render(request, 'core/dashboards/admin.html')


@login_required
@docente_required
def docente_dashboard(request):
    """Docente dashboard view."""
    from .models import Materia
    materias = Materia.objects.select_related('carrera', 'docente').prefetch_related('inscripciones').filter(docente=request.user)
    context = {
        'materias': materias,
    }
    return render(request, 'core/dashboards/docente.html', context)


@login_required
@alumno_required
def alumno_dashboard(request):
    """Alumno dashboard view."""
    return render(request, 'core/dashboards/alumno.html')


@login_required
@preceptor_required
def preceptor_dashboard(request):
    """Preceptor dashboard view."""
    return render(request, 'core/dashboards/preceptor.html')


@login_required
@docente_required
def mis_materias(request):
    """
    Lista las materias asignadas al docente autenticado.
    """
    materias = []
    if request.user.is_authenticated:
        # Materias donde el usuario es docente y están activas
        from .models import Materia
        materias = Materia.objects.select_related('carrera', 'docente').prefetch_related('inscripciones').filter(docente=request.user)

    context = {
        'materias': materias,
        'title': 'Mis Materias',
    }
    return render(request, 'core/docente/mis_materias.html', context)
