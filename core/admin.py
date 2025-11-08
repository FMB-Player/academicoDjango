from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from .models import Usuario, Carrera, Materia, Inscripcion, InscripcionCarrera


class CustomAdminSite(admin.AdminSite):
    """Custom admin site that shows 403 for non-staff users."""
    
    @never_cache
    def login(self, request, extra_context=None):
        """
        Override the login view to redirect non-staff users to 404.
        """
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                self.login_url or reverse('admin:login', current_app=self.name)
            )
        if not request.user.is_staff:
            return HttpResponseForbidden(
                'You do not have permission to access this page.',
                content_type='text/plain'
            )
        return super().login(request, extra_context)
    
    def admin_view(self, view, cacheable=False):
        """
        Override admin_view to check for staff status.
        """
        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                # For non-staff users, show 404 for masking
                from django.views.defaults import permission_denied
                return permission_denied(request, None, template_name='core/errors/404.html')
            
            return view(request, *args, **kwargs)
        
        if not cacheable:
            inner = never_cache(inner)
        # Mark the view with the admin's name for backwards compatibility.
        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)
        return inner
    
    def logout(self, request, extra_context=None):
        """
        Override the logout view to redirect to home page.
        """
        from django.contrib.auth import logout
        from django.http import HttpResponseRedirect
        
        logout(request)
        return HttpResponseRedirect('/')


class UsuarioAdmin(UserAdmin):
    list_display = ('email', 'dni', 'nombre', 'apellido', 'rol', 'is_active')
    list_filter = ('rol', 'is_active')
    search_fields = ('email', 'dni', 'nombre', 'apellido')
    ordering = ('email', 'apellido', 'nombre')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información personal'), {'fields': ('dni', 'nombre', 'apellido', 'fecha_nacimiento')}),
        (_('Información de contacto'), {'fields': ('telefono', 'direccion')}),
        (_('Permisos'), {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Fechas importantes'), {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'dni', 'nombre', 'apellido', 'password1', 'password2', 'rol'),
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        
        if not is_superuser:
            # Remove superuser and staff status from non-superusers
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'is_staff' in form.base_fields:
                form.base_fields['is_staff'].disabled = True
        
        return form


class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion', 'cupo_maximo', 'is_active', 'alumnos_inscriptos')
    list_filter = ('is_active',)
    search_fields = ('nombre',)
    actions = ['activar_carreras', 'desactivar_carreras']
    
    def alumnos_inscriptos(self, obj):
        return obj.inscripciones_carrera.activas().count()
    alumnos_inscriptos.short_description = _('Alumnos inscriptos')
    
    @admin.action(description=_('Activar carreras seleccionadas'))
    def activar_carreras(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} carreras activadas correctamente.")
    
    @admin.action(description=_('Desactivar carreras seleccionadas'))
    def desactivar_carreras(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} carreras desactivadas correctamente.")
    
    def has_delete_permission(self, request, obj=None):
        if obj and not obj.puede_eliminarse():
            return False
        return super().has_delete_permission(request, obj)


class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'mostrar_carreras', 'docente', 'cupo_disponible', 'is_active')
    list_filter = ('carreras', 'is_active')
    search_fields = ('nombre', 'carreras__nombre', 'docente__apellido', 'docente__nombre')
    filter_horizontal = ('carreras',)
    list_select_related = ('docente',)
    raw_id_fields = ('docente',)
    actions = ['activar_materias', 'desactivar_materias']
    
    def mostrar_carreras(self, obj):
        return ", ".join([c.nombre for c in obj.carreras.all()])
    mostrar_carreras.short_description = _('Carreras')
    
    def cupo_disponible(self, obj):
        return f"{obj.inscripciones.activas().count()} / {obj.cupo_maximo}"
    cupo_disponible.short_description = _('Cupo')
    
    def activar_materias(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} materias activadas correctamente.")
    activar_materias.short_description = _("Activar materias seleccionadas")
    
    def desactivar_materias(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} materias desactivadas correctamente.")
    desactivar_materias.short_description = _("Desactivar materias seleccionadas")
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'docente':
            kwargs['queryset'] = Usuario.objects.filter(rol=Usuario.Rol.DOCENTE, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'carreras':
            kwargs['queryset'] = Carrera.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def has_delete_permission(self, request, obj=None):
        # Solo permitir eliminar si no hay inscripciones activas
        if obj and obj.inscripciones.activas().exists():
            return False
        return super().has_delete_permission(request, obj)


class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'materia', 'carreras_materia', 'fecha_inscripcion', 'is_active')
    list_filter = ('materia__carreras', 'is_active')
    search_fields = (
        'alumno__dni', 'alumno__apellido', 'alumno__nombre',
        'materia__nombre', 'materia__carreras__nombre'
    )
    list_select_related = ('alumno', 'materia')
    raw_id_fields = ('alumno', 'materia')
    date_hierarchy = 'fecha_inscripcion'
    actions = ['activar_inscripciones', 'desactivar_inscripciones']
    
    def carreras_materia(self, obj):
        return ", ".join([c.nombre for c in obj.materia.carreras.all()])
    carreras_materia.short_description = _('Carreras')
    
    @admin.action(description=_('Activar inscripciones seleccionadas'))
    def activar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} inscripciones activadas correctamente.")
    
    @admin.action(description=_('Desactivar inscripciones seleccionadas'))
    def desactivar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} inscripciones desactivadas correctamente.")


class InscripcionCarreraAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'carrera', 'fecha_inscripcion', 'is_active')
    list_filter = ('carrera', 'is_active')
    search_fields = (
        'alumno__dni', 'alumno__apellido', 'alumno__nombre',
        'carrera__nombre'
    )
    list_select_related = ('alumno', 'carrera')
    raw_id_fields = ('alumno', 'carrera')
    date_hierarchy = 'fecha_inscripcion'
    actions = ['activar_inscripciones', 'desactivar_inscripciones']
    
    @admin.action(description=_('Activar inscripciones seleccionadas'))
    def activar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} inscripciones activadas correctamente.")
    
    @admin.action(description=_('Desactivar inscripciones seleccionadas'))
    def desactivar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} inscripciones desactivadas correctamente.")


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='customadmin')

# Register Group model with custom admin site
custom_admin_site.register(Group, GroupAdmin)

# Register models with the custom admin site
custom_admin_site.register(Usuario, UsuarioAdmin)
custom_admin_site.register(Carrera, CarreraAdmin)
custom_admin_site.register(Materia, MateriaAdmin)
custom_admin_site.register(Inscripcion, InscripcionAdmin)
custom_admin_site.register(InscripcionCarrera, InscripcionCarreraAdmin)
