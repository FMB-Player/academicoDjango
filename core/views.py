from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.utils import timezone
from .decorators import admin_required, docente_required, alumno_required, preceptor_required
from .forms import ProfileEditForm, CustomPasswordChangeForm
from .models import Materia, Usuario, Carrera, InscripcionCarrera, Inscripcion


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


@login_required
def change_password(request):
    """
    Change user password.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to prevent user from being logged out
            update_session_auth_hash(request, user)
            # Update the flag
            user.debe_cambiar_password = False
            user.save()
            messages.success(request, 'Tu contraseña ha sido actualizada exitosamente.')
            return redirect('core:perfil')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'core/auth/change_password.html', {'form': form})


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
        return redirect('core:admin_dashboard')
    elif request.user.rol == 'DOCENTE':
        return redirect('core:docente_dashboard')
    elif request.user.rol == 'ALUMNO':
        return redirect('core:alumno_dashboard')
    elif request.user.rol == 'PRECEPTOR':
        return redirect('core:preceptor_dashboard')
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
def desinscribir_materia(request, materia_id):
    """Desinscribir a un alumno de una materia específica."""
    materia = get_object_or_404(Materia, id=materia_id, is_active=True)
    
    # Buscar la inscripción activa del alumno
    try:
        inscripcion = Inscripcion.objects.get(
            alumno=request.user,
            materia=materia,
            is_active=True
        )
        # Desactivar la inscripción (baja lógica)
        inscripcion.is_active = False
        inscripcion.save()
        messages.success(request, f'Te has desinscripto de {materia.nombre}')
    except Inscripcion.DoesNotExist:
        messages.error(request, 'No estás inscripto en esta materia')
    
    return redirect('core:alumno_dashboard')


@login_required
@alumno_required
def desinscribir_carrera(request, carrera_id):
    """Desinscribir a un alumno de una carrera específica."""
    carrera = get_object_or_404(Carrera, id=carrera_id, is_active=True)
    
    # Verificar que no tenga inscripciones activas a materias de esta carrera
    inscripciones_activas = Inscripcion.objects.filter(
        alumno=request.user,
        materia__carreras=carrera,
        is_active=True,
        materia__is_active=True
    ).exists()
    
    if inscripciones_activas:
        messages.error(request, 
            f'No puedes desinscribirte de {carrera.nombre} porque todavía tienes materias activas. '
            f'Desinscríbete primero de todas las materias de esta carrera.'
        )
    else:
        try:
            inscripcion_carrera = InscripcionCarrera.objects.get(
                alumno=request.user,
                carrera=carrera,
                is_active=True
            )
            # Desactivar la inscripción a la carrera (baja lógica)
            inscripcion_carrera.is_active = False
            inscripcion_carrera.save()
            messages.success(request, f'Te has desinscripto de {carrera.nombre}')
        except InscripcionCarrera.DoesNotExist:
            messages.error(request, 'No estás inscripto en esta carrera')
    
    return redirect('core:alumno_dashboard')


@login_required
@alumno_required
def inscribir_materia(request, materia_id):
    """Inscribir a un alumno en una materia específica."""
    materia = get_object_or_404(Materia, id=materia_id, is_active=True)
    
    # Verificar que el alumno esté inscripto en alguna carrera de esta materia
    carreras_comunes = materia.carreras.filter(
        inscripciones_carrera__alumno=request.user,
        inscripciones_carrera__is_active=True,
        is_active=True
    )
    
    if not carreras_comunes.exists():
        messages.error(request, 
            f'No puedes inscribirte en {materia.nombre} porque no estás inscripto en ninguna carrera que contenga esta materia'
        )
        return redirect('core:alumno_dashboard')
    
    # Verificar que ya no esté inscripto
    if Inscripcion.objects.filter(alumno=request.user, materia=materia, is_active=True).exists():
        messages.warning(request, f'Ya estás inscripto en {materia.nombre}')
        return redirect('core:alumno_dashboard')
    
    # Verificar cupo
    inscripciones_activas = materia.inscripciones.filter(is_active=True).count()
    if inscripciones_activas >= materia.cupo_maximo:
        messages.error(request, f'No hay cupo disponible en {materia.nombre}')
        return redirect('core:alumno_dashboard')
    
    # Crear la inscripción
    Inscripcion.objects.create(
        alumno=request.user,
        materia=materia,
        fecha_inscripcion=timezone.now()
    )
    
    messages.success(request, f'Te has inscripto exitosamente en {materia.nombre}')
    return redirect('core:alumno_dashboard')


@login_required
@alumno_required
def alumno_dashboard(request):
    """Alumno dashboard view - simplified version."""
    # Get the student's active career enrollments only
    carreras_inscripto = request.user.carreras_inscripciones.filter(
        is_active=True
    ).annotate(
        materias_inscriptas_count=Count(
            'carrera__materias',
            filter=Q(
                carrera__materias__inscripciones__alumno=request.user,
                carrera__materias__inscripciones__is_active=True,
                carrera__materias__is_active=True
            ),
            distinct=True
        ),
        materias_totales_count=Count(
            'carrera__materias',
            filter=Q(carrera__materias__is_active=True),
            distinct=True
        )
    )
    
    # Get the student's active subject enrollments
    materias_inscriptas = Materia.objects.filter(
        inscripciones__alumno=request.user,
        inscripciones__is_active=True,
        is_active=True
    ).prefetch_related('carreras').distinct()
    
    context = {
        'carreras_inscripto': carreras_inscripto,
        'materias_inscriptas': materias_inscriptas,
    }
    return render(request, 'core/dashboards/alumno.html', context)


@login_required
@preceptor_required
def preceptor_dashboard(request):
    """Preceptor dashboard view."""
    return render(request, 'core/dashboards/preceptor.html')


@login_required
@docente_required
def docente_mis_materias(request):
    """
    Lista las materias asignadas al docente autenticado.
    """
    try:
        # Obtener solo las materias activas del docente actual con prefetch_related para carreras
        materias = Materia.objects.filter(
            docente=request.user,
            is_active=True
        ).prefetch_related('carreras')
        
        # Anotar el número de alumnos activos en cada materia
        materias = materias.annotate(
            num_alumnos=Count('inscripciones', filter=Q(inscripciones__is_active=True))
        )
        
        # Ordenar por nombre de materia
        materias = materias.order_by('nombre')
        
        context = {
            'materias': materias,
            'title': 'Mis Materias',
        }
        
        return render(request, 'core/docente/mis_materias.html', context)
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error en mis_materias (docente): {str(e)}")
        messages.error(request, 'Ocurrió un error al cargar las materias. Por favor, intente nuevamente.')
        return redirect('core:docente_dashboard')


@login_required
@docente_required
def docente_detalle_materia(request, materia_id):
    """
    Muestra el detalle de una materia específica para el docente.
    """
    try:
        # Get the subject with related carreras, ensuring it belongs to the current docente
        materia = get_object_or_404(
            Materia.objects.prefetch_related('carreras', 'inscripciones__alumno'),
            id=materia_id,
            docente=request.user,
            is_active=True
        )
        
        # Get active enrollments with student info
        inscripciones = materia.inscripciones.filter(is_active=True).select_related('alumno')
        
        context = {
            'materia': materia,
            'inscripciones': inscripciones,
            'total_alumnos': inscripciones.count(),
            'hoy': timezone.now().date()
        }
        
        return render(request, 'core/docente/detalle_materia.html', context)
        
    except Exception as e:
        print(f"Error en detalle_materia (docente): {str(e)}")
        messages.error(request, 'Ocurrió un error al cargar los detalles de la materia.')
        return redirect('core:docente_mis_materias')


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
    # inscripciones = materia.inscripciones.filter(is_active=True).select_related('alumno')
    # Currently not ever used. Don't delete, we might use later.
    
    if request.method == 'POST':
        # Placeholder for actual attendance logic
        messages.success(request, 'Asistencia registrada correctamente')
        return redirect('core:detalle_materia', materia_id=materia.id)
    
    """ context = {
        'materia': materia,
        'inscripciones': inscripciones,
        'hoy': timezone.now().date()
    } """
    # Currently not ever used. Don't delete, we might use later.
    
    # For now, redirect to detail page with a message
    messages.info(request, 'La funcionalidad de toma de asistencia estará disponible próximamente')
    return redirect('core:detalle_materia', materia_id=materia.id)


@login_required
@alumno_required
def mis_materias(request):
    """
    Muestra las materias en las que el alumno está inscrito con opciones de gestión.
    """
    try:
        # Obtener las carreras activas del alumno con información de desinscripción
        carreras_inscrito = request.user.carreras_inscripciones.filter(
            is_active=True
        ).annotate(
            materias_inscriptas_count=Count(
                'carrera__materias',
                filter=Q(
                    carrera__materias__inscripciones__alumno=request.user,
                    carrera__materias__inscripciones__is_active=True,
                    carrera__materias__is_active=True
                ),
                distinct=True
            ),
            materias_totales_count=Count(
                'carrera__materias',
                filter=Q(carrera__materias__is_active=True),
                distinct=True
            )
        )
        
        # Para cada carrera, verificar si puede desinscribirse y obtener materias no inscriptas
        for carrera_insc in carreras_inscrito:
            # Verificar si puede desinscribirse (no tiene materias activas)
            inscripciones_activas = Inscripcion.objects.filter(
                alumno=request.user,
                materia__carreras=carrera_insc.carrera,
                is_active=True,
                materia__is_active=True
            ).exists()
            carrera_insc.puede_desinscribirse = not inscripciones_activas
            
            # Obtener materias no inscriptas de esta carrera
            materias_inscriptas_ids = Inscripcion.objects.filter(
                alumno=request.user,
                is_active=True,
                materia__is_active=True,
                materia__carreras=carrera_insc.carrera
            ).values_list('materia_id', flat=True)
            
            carrera_insc.materias_no_inscriptas = Materia.objects.filter(
                carreras=carrera_insc.carrera,
                is_active=True
            ).exclude(
                id__in=materias_inscriptas_ids
            ).annotate(
                cupo_actual=Count('inscripciones', filter=Q(inscripciones__is_active=True))
            )
        
        # Obtener las inscripciones activas del alumno a materias
        inscripciones = Inscripcion.objects.filter(
            alumno=request.user,
            is_active=True,
            materia__is_active=True
        ).select_related('materia', 'materia__docente').prefetch_related('materia__carreras')
        
        # Agregar información adicional a cada materia
        for inscripcion in inscripciones:
            inscripcion.materia.inscriptos_count = inscripcion.materia.inscripciones.activas().count()
            inscripcion.materia.carreras_comunes = inscripcion.materia.carreras.filter(
                inscripciones_carrera__alumno=request.user,
                inscripciones_carrera__is_active=True,
                is_active=True
            )
        
        context = {
            'carreras_inscrito': carreras_inscrito,
            'inscripciones': inscripciones,
            'title': 'Mis Materias',
        }
        
        return render(request, 'core/alumno/mis_materias.html', context)
        
    except Exception as e:
        print(f"Error en mis_materias (alumno): {str(e)}")
        messages.error(request, 'Ocurrió un error al cargar tus materias.')
        return redirect('core:alumno_dashboard')


@login_required
@alumno_required
def detalle_materia(request, materia_id):
    """
    Muestra el detalle de una materia específica para el alumno.
    """
    try:
        # Verificar que el alumno esté inscripto en la materia
        materia = get_object_or_404(
            Materia.objects.prefetch_related('carreras', 'docente'),
            id=materia_id,
            inscripciones__alumno=request.user,
            inscripciones__is_active=True,
            is_active=True
        )
        
        # Obtener información de la inscripción del alumno
        inscripcion = materia.inscripciones.get(
            alumno=request.user,
            is_active=True
        )
        
        # Calcular porcentaje de asistencia (placeholder)
        porcentaje_asistencia = 85  # Esto debería calcularse con datos reales
        
        # Calcular promedio (placeholder)
        promedio = 7.5  # Esto debería calcularse con datos reales
        
        context = {
            'materia': materia,
            'inscripcion': inscripcion,
            'porcentaje_asistencia': porcentaje_asistencia,
            'promedio': promedio,
            'hoy': timezone.now().date()
        }
        
        return render(request, 'core/alumno/detalle_materia.html', context)
        
    except Exception as e:
        print(f"Error en detalle_materia (alumno): {str(e)}")
        messages.error(request, 'No se pudo cargar la información de la materia.')
        return redirect('core:mis_materias')


@login_required
@alumno_required
def materias_inscripcion(request):
    """
    Permite al alumno ver e inscribirse a materias disponibles.
    """
    # Obtener las carreras en las que el alumno está inscripto
    carreras_inscritas = request.user.carreras_inscripto.filter(
        inscripciones_carrera__is_active=True
    )
    
    # Si no está inscripto en ninguna carrera, redirigir con mensaje
    if not carreras_inscritas.exists():
        messages.warning(
            request,
            'Debes estar inscripto en al menos una carrera para poder inscribirte a materias.'
        )
        return redirect('core:carreras')
    
    # Obtener las materias en las que ya está inscripto el alumno
    materias_inscriptas = Materia.objects.filter(
        inscripciones__alumno=request.user,
        inscripciones__is_active=True
    )
    
    # Obtener materias disponibles para inscribirse
    # Son las materias de las carreras en las que está inscripto,
    # que no esté ya inscripto, y que estén activas
    materias_disponibles = Materia.objects.filter(
        carreras__in=carreras_inscritas,
        is_active=True
    ).exclude(
        id__in=materias_inscriptas.values_list('id', flat=True)
    ).distinct()
    
    # Manejar la inscripción a una materia
    if request.method == 'POST' and 'materia_id' in request.POST:
        try:
            materia_id = request.POST.get('materia_id')
            materia = Materia.objects.get(
                id=materia_id,
                carreras__in=carreras_inscritas,
                is_active=True
            )
            
            # Verificar si ya existe una inscripción inactiva
            inscripcion_existente = Inscripcion.objects.filter(
                alumno=request.user,
                materia=materia
            ).first()
            
            if inscripcion_existente:
                # Si existe una inscripción inactiva, reactivarla
                if not inscripcion_existente.is_active:
                    inscripcion_existente.is_active = True
                    inscripcion_existente.save()
                    messages.success(request, f'Te has inscripto a {materia.nombre} correctamente.')
                else:
                    messages.info(request, f'Ya estás inscripto en {materia.nombre}.')
            else:
                # Crear nueva inscripción
                Inscripcion.objects.create(
                    alumno=request.user,
                    materia=materia,
                    is_active=True
                )
                messages.success(request, f'Te has inscripto a {materia.nombre} correctamente.')
            
            return redirect('core:materias_inscripcion')
            
        except Materia.DoesNotExist:
            messages.error(request, 'La materia seleccionada no es válida o no está disponible.')
        except Exception as e:
            messages.error(request, f'Error al inscribirse a la materia: {str(e)}')
    
    context = {
        'materias_inscriptas': materias_inscriptas,
        'materias_disponibles': materias_disponibles,
        'carreras_inscritas': carreras_inscritas
    }
    
    return render(request, 'core/alumno/materias_inscripcion.html', context)


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
    messages.info(request, f'Vista de detalle del alumno {alumno.nombre} {alumno.apellido} (placeholder)')
    return render(request, 'core/preceptor/detalle_alumno.html', {'alumno': alumno})


def notificar_alumno(request, alumno_id):
    """
    Permite al preceptor notificar a un alumno.
    """
    if not hasattr(request.user, 'preceptor'):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('core:home')
    
    # Placeholder implementation
    messages.info(request, 'Próximamente: Notificación a alumno')
    return render(request, 'core/preceptor/notificar_alumno.html')


def carreras(request):
    """
    Muestra el listado de todas las carreras disponibles.
    Los usuarios pueden ver las carreras, y los alumnos pueden inscribirse.
    """
    carreras = Carrera.objects.filter(is_active=True).order_by('nombre')
    
    # Check if user is authenticated and is an alumno
    user_subscriptions = set()
    if request.user.is_authenticated and hasattr(request.user, 'rol') and request.user.rol == Usuario.Rol.ALUMNO:
        user_subscriptions = set(
            InscripcionCarrera.objects.filter(
                alumno=request.user,
                is_active=True
            ).values_list('carrera_id', flat=True)
        )
    
    context = {
        'carreras': carreras,
        'user_subscriptions': user_subscriptions,
        'is_alumno': request.user.is_authenticated and hasattr(request.user, 'rol') and request.user.rol == Usuario.Rol.ALUMNO,
        'title': 'Carreras Disponibles'
    }
    return render(request, 'core/carreras/lista.html', context)


@login_required
def inscribir_carrera(request, carrera_id):
    """
    Maneja la inscripción de un alumno a una carrera.
    Si ya existe una inscripción inactiva, la reactiva.
    Si ya está activa, redirige al dashboard.
    Si no existe, crea una nueva.
    """
    if request.user.rol != Usuario.Rol.ALUMNO:
        messages.error(request, 'Solo los alumnos pueden inscribirse a carreras.')
        return redirect('core:carreras')
    
    carrera = get_object_or_404(Carrera, id=carrera_id, is_active=True)
    
    # Check for existing subscription (active or inactive)
    try:
        inscripcion = InscripcionCarrera.objects.get(
            alumno=request.user,
            carrera=carrera
        )
        
        if inscripcion.is_active:
            messages.info(request, f'Ya estás inscripto en la carrera {carrera.nombre}.')
            return redirect('core:mis_materias')
        else:
            # Reactivar la inscripción existente
            inscripcion.is_active = True
            inscripcion.fecha_inscripcion = timezone.now()  # Actualizar la fecha
            inscripcion.save()
            message = f'¡Has reactivado tu inscripción a {carrera.nombre}!'
            
    except InscripcionCarrera.DoesNotExist:
        # Crear nueva inscripción
        try:
            InscripcionCarrera.objects.create(
                alumno=request.user,
                carrera=carrera
            )
            message = f'¡Te has inscripto exitosamente a {carrera.nombre!r}!' 
        except Exception as e:
            messages.error(request, f'Error al inscribirse a la carrera: {str(e)}')
            return redirect('core:carreras')
    
    # Auto-subscribe to available subjects
    from .utils import auto_subscribe_to_available_subjects
    success_count, skipped_count, errors = auto_subscribe_to_available_subjects(
        request.user, carrera_id
    )
    
    # Add success message with subscription details
    messages.success(request, message)
    if success_count > 0:
        messages.success(
            request,
            f'Te hemos inscripto automáticamente en {success_count} materia(s) disponible(s).'
        )
    if skipped_count > 0:
        messages.info(
            request,
            f'{skipped_count} materia(s) no tienen cupo disponible actualmente.'
        )
    for error in errors:
        messages.warning(request, error)
    
    return redirect('core:materias_inscripcion')
