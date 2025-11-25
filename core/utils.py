from django.db import transaction
from django.utils import timezone
from .models import Inscripcion, Materia, Carrera

def auto_subscribe_to_available_subjects(alumno, carrera_id):
    """
    Auto-subscribes a student to all available subjects in the specified career
    that haven't reached their maximum capacity.
    
    Args:
        alumno: The student (Usuario instance with rol=ALUMNO)
        carrera_id: ID of the career to subscribe to
        
    Returns:
        tuple: (success_count, skipped_count, error_messages)
    """
    success_count = 0
    skipped_count = 0
    error_messages = []
    
    try:
        carrera = Carrera.objects.get(id=carrera_id, is_active=True)
    except Carrera.DoesNotExist:
        error_messages.append(f'Carrera con ID {carrera_id} no encontrada o inactiva')
        return 0, 0, error_messages
    
    # Get all active subjects in this career
    materias_carrera = Materia.objects.filter(
        carreras=carrera,
        is_active=True
    )
    
    with transaction.atomic():
        for materia in materias_carrera:
            # Check if already enrolled
            if Inscripcion.objects.filter(
                alumno=alumno,
                materia=materia,
                is_active=True
            ).exists():
                skipped_count += 1
                continue
                
            # Check current enrollment count
            current_enrollment = materia.inscripciones.filter(is_active=True).count()
            if current_enrollment >= materia.cupo_maximo:
                skipped_count += 1
                continue
                
            # Check for existing inactive enrollment
            try:
                inscripcion = Inscripcion.objects.get(
                    alumno=alumno,
                    materia=materia
                )
                # Reactivate existing enrollment
                inscripcion.is_active = True
                inscripcion.fecha_inscripcion = timezone.now()
                inscripcion.save()
                success_count += 1
                
            except Inscripcion.DoesNotExist:
                # Create new enrollment
                try:
                    Inscripcion.objects.create(
                        alumno=alumno,
                        materia=materia
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f'Error inscribiendo a {materia.nombre}: {str(e)}')
    
    return success_count, skipped_count, error_messages
