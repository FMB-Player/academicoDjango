from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Persona(models.Model):
    """
    Abstract base class for all person types in the system.
    """
    dni = models.PositiveIntegerField(
        _('DNI'),
        unique=True,
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)]
    )
    nombre = models.CharField(_('nombre'), max_length=50)
    apellido = models.CharField(_('apellido'), max_length=50)
    fecha_nacimiento = models.DateField(_('fecha de nacimiento'), null=True, blank=True)
    telefono = models.CharField(_('teléfono'), max_length=20, blank=True)
    direccion = models.TextField(_('dirección'), blank=True)
    email = models.EmailField(_('email'), unique=True)

    class Meta:
        abstract = True
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class UsuarioManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El email es obligatorio'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password or str(extra_fields.get('dni', '')))
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('rol', self.model.Rol.ADMIN)  # Set default role to ADMIN
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser, Persona):
    """Custom user model that uses email as the unique identifier."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Remove fields from AbstractUser that are in Persona
    first_name = None
    last_name = None
    date_joined = None
    
    # User roles
    class Rol(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        ALUMNO = 'ALUMNO', _('Alumno')
        DOCENTE = 'DOCENTE', _('Docente')
        PRECEPTOR = 'PRECEPTOR', _('Preceptor')
    
    rol = models.CharField(
        _('rol'),
        max_length=10,
        choices=Rol.choices,
        default=Rol.ALUMNO
    )
    
    # Track if the user needs to change their password
    debe_cambiar_password = models.BooleanField(
        _('debe cambiar contraseña'),
        default=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['dni', 'nombre', 'apellido']
    
    objects = UsuarioManager()
    
    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.get_rol_display()})"


class Carrera(models.Model):
    """Represents a degree program."""
    nombre = models.CharField(_('nombre'), max_length=100, unique=True)
    duracion = models.PositiveSmallIntegerField(
        _('duración en años'),
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    cupo_maximo = models.PositiveSmallIntegerField(
        _('cupo máximo de alumnos'),
        default=100
    )
    is_active = models.BooleanField(_('activa'), default=True)
    
    class Meta:
        verbose_name = _('carrera')
        verbose_name_plural = _('carreras')
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def puede_eliminarse(self):
        """Check if the career can be deleted."""
        # Usa el related_name real 'inscripciones_carrera'
        return not (self.materias.exists() or self.inscripciones_carrera.exists())


class Materia(models.Model):
    """Represents a course/subject that can belong to multiple carreras."""
    nombre = models.CharField(
        _('nombre'), 
        max_length=100,
        unique=True,
        help_text=_('Nombre único de la materia')
    )
    carreras = models.ManyToManyField(
        Carrera,
        related_name='materias',
        verbose_name=_('carreras')
    )
    docente = models.ForeignKey(
        'core.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'rol': Usuario.Rol.DOCENTE},
        related_name='materias_dictadas',
        verbose_name=_('docente')
    )
    cupo_maximo = models.PositiveSmallIntegerField(
        _('cupo máximo de alumnos'),
        default=30,
        help_text=_('Número máximo de alumnos que pueden inscribirse a esta materia')
    )
    is_active = models.BooleanField(_('activa'), default=True)
    
    class Meta:
        verbose_name = _('materia')
        verbose_name_plural = _('materias')
        ordering = ['nombre']
    
    def __str__(self):
        carreras = ", ".join(str(carrera) for carrera in self.carreras.all()[:3])
        if self.carreras.count() > 3:
            carreras += "..."
        return f"{self.nombre} ({carreras})"
    
    def puede_eliminarse(self):
        """Check if the subject can be deleted."""
        return not self.inscripciones.exists()


class InscripcionQuerySet(models.QuerySet):
    def activas(self):
        return self.filter(is_active=True)


class Inscripcion(models.Model):
    """Represents a student's enrollment in a subject."""
    alumno = models.ForeignKey(
        'core.Usuario',
        on_delete=models.CASCADE,
        limit_choices_to={'rol': Usuario.Rol.ALUMNO},
        related_name='inscripciones',
        verbose_name=_('alumno')
    )
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name=_('materia')
    )
    fecha_inscripcion = models.DateTimeField(
        _('fecha de inscripción'),
        auto_now_add=True
    )
    is_active = models.BooleanField(_('activa'), default=True)
    
    # Manager por defecto que expone QuerySet.activas() también en los related managers
    objects = InscripcionQuerySet.as_manager()
    
    class Meta:
        verbose_name = _('inscripción')
        verbose_name_plural = _('inscripciones')
        unique_together = ['alumno', 'materia']
    
    def __str__(self):
        return f"{self.alumno} - {self.materia}"
    
    def save(self, *args, **kwargs):
        """Override save to validate enrollment constraints."""
        # Check if the student is enrolled in the career
        carrera_alumno = self.alumno.carreras_inscripto.first()
        if not carrera_alumno or carrera_alumno.carrera != self.materia.carrera:
            raise ValueError("El alumno no está inscripto en la carrera de esta materia")
            
        # Check if there's available space
        if self.materia.inscripciones.activas().count() >= self.materia.cupo_maximo:
            raise ValueError("No hay cupo disponible en esta materia")
            
        super().save(*args, **kwargs)


class InscripcionCarreraQuerySet(models.QuerySet):
    def activas(self):
        return self.filter(is_active=True)


class InscripcionCarrera(models.Model):
    """Represents a student's enrollment in a career."""
    alumno = models.ForeignKey(
        'core.Usuario',
        on_delete=models.CASCADE,
        limit_choices_to={'rol': Usuario.Rol.ALUMNO},
        related_name='carreras_inscripciones',
        verbose_name=_('alumno')
    )
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.CASCADE,
        related_name='inscripciones_carrera',
        verbose_name=_('carrera')
    )
    fecha_inscripcion = models.DateTimeField(
        _('fecha de inscripción'),
        auto_now_add=True
    )
    is_active = models.BooleanField(_('activa'), default=True)
    
    objects = InscripcionCarreraQuerySet.as_manager()
    
    class Meta:
        verbose_name = _('inscripción a carrera')
        verbose_name_plural = _('inscripciones a carreras')
        unique_together = ['alumno', 'carrera']
    
    def __str__(self):
        return f"{self.alumno} - {self.carrera}"
    
    def save(self, *args, **kwargs):
        """Override save to validate career enrollment constraints."""
        if self.alumno.rol != Usuario.Rol.ALUMNO:
            raise ValueError("Solo los alumnos pueden inscribirse a carreras")
            
        if self.is_active and self.carrera.inscripciones_carrera.activas().count() >= self.carrera.cupo_maximo:
            raise ValueError("No hay cupo disponible en esta carrera")
            
        super().save(*args, **kwargs)


# Add related names to Usuario for reverse relationships
Usuario.add_to_class('carreras_inscripto', models.ManyToManyField(
    Carrera,
    through='core.InscripcionCarrera',
    related_name='alumnos',
    verbose_name=_('carreras inscripto')
))
