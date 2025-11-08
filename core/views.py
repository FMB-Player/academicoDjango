from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.utils import timezone
from .decorators import admin_required, docente_required, alumno_required, preceptor_required
from .forms import ProfileEditForm
from .models import Materia, Usuario


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
                messages.success(request, f'Bienvenido, {(str(user.nombre) + " " + str(user.apellido)) or user.email}!')
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
    materias = Materia.objects.filter(
        docente=request.user,
        is_active=True
    ).prefetch_related('carreras', 'inscripciones')
    
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
    # Check if user has the DOCENTE role
    if request.user.rol != Usuario.Rol.DOCENTE:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('core:home')
    
    # Get all active subjects for the current teacher with related data
    materias = Materia.objects.filter(
        docente=request.user,
        is_active=True
    ).prefetch_related('carreras')
    
    # Annotate with the count of active enrollments
    materias = materias.annotate(
        num_alumnos=Count('inscripciones', filter=Q(inscripciones__is_active=True))
    )
    
    context = {
        'materias': materias,
    }
    return render(request, 'core/docente/mis_materias.html', context)


@login_required
@docente_required
def detalle_materia(request, materia_id):
    """
    Muestra el detalle de una materia específica para el docente.
    """
    # Get the subject with related carreras, ensuring it belongs to the current docente
    materia = get_object_or_404(
        Materia.objects.prefetch_related('carreras'), 
        id=materia_id,
        docente=request.user,
        is_active=True
    )
    
    # Get active enrollments with student info
    inscripciones = materia.inscripciones.filter(
        is_active=True
    ).select_related('alumno')
    
    context = {
        'materia': materia,
        'inscripciones': inscripciones,
        'total_alumnos': inscripciones.count(),
        'hoy': timezone.now().date()
    }
    
    return render(request, 'core/docente/detalle_materia.html', context)


@login_required
@docente_required
def tomar_asistencia(request, materia_id):
    """
    Permite al docente tomar asistencia para una materia específica.
    """
    # Get the materia with related data, ensuring it belongs to the current docente
    materia = get_object_or_404(
        Materia.objects.prefetch_related('carreras', 'inscripciones__alumno'),
        id=materia_id,
        docente=request.user,
        is_active=True
    )
    
    # Get active enrollments with student info
    inscripciones = materia.inscripciones.filter(is_active=True).select_related('alumno')
    
    if request.method == 'POST':
        # Placeholder for actual attendance logic
        messages.success(request, 'Asistencia registrada correctamente')
        return redirect('core:detalle_materia', materia_id=materia.id)
    
    context = {
        'materia': materia,
        'inscripciones': inscripciones,
        'hoy': timezone.now().date()
    }
    
    # For now, redirect to detail page with a message
    messages.info(request, 'La funcionalidad de toma de asistencia estará disponible próximamente')
    return redirect('core:detalle_materia', materia_id=materia.id)


def materias_inscripcion(request):
    """
    Permite al alumno ver e inscribirse a materias disponibles.
    """
    if not hasattr(request.user, 'alumno'):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('core:home')
    
    # Placeholder implementation
    messages.info(request, 'Vista de inscripción a materias (placeholder)')
    return render(request, 'core/alumno/materias_inscripcion.html')


def novedades(request):
    """
    Muestra las novedades y notificaciones para el preceptor.
    """
    if not hasattr(request.user, 'preceptor'):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('core:home')
    
    # Placeholder implementation
    messages.info(request, 'Vista de novedades (placeholder)')
    return render(request, 'core/preceptor/novedades.html')


def informe_inasistencias(request):
    """
    Muestra un informe de inasistencias para el preceptor.
    """
    if not hasattr(request.user, 'preceptor'):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('core:home')
    
    # Placeholder implementation
    messages.info(request, 'Vista de informe de inasistencias (placeholder)')
    return render(request, 'core/preceptor/informe_inasistencias.html')


def detalle_alumno(request, alumno_id):
    """
    Muestra el detalle de un alumno para el preceptor.
    """
    if not hasattr(request.user, 'preceptor'):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('core:home')
    
    # Placeholder implementation
    alumno = get_object_or_404(Usuario, id=alumno_id)
    messages.info(request, f'Vista de detalle del alumno {alumno.get_full_name()} (placeholder)')
    return render(request, 'core/preceptor/detalle_alumno.html', {'alumno': alumno})


def notificar_alumno(request, alumno_id):
    """
    Permite al preceptor notificar a un alumno.
    """
    if not hasattr(request.user, 'preceptor'):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('core:home')
    
    # Placeholder implementation
    alumno = get_object_or_404(Usuario, id=alumno_id)
    messages.info(request, f'Vista de notificación al alumno {alumno.get_full_name()} (placeholder)')
    return render(request, 'core/preceptor/notificar_alumno.html', {'alumno': alumno})
