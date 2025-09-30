from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario, Carrera, Materia, Inscripcion, InscripcionCarrera


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
    list_display = ('nombre', 'duracion', 'cupo_maximo', 'activa', 'alumnos_inscriptos')
    list_filter = ('activa',)
    search_fields = ('nombre',)
    actions = ['activar_carreras', 'desactivar_carreras']
    
    def alumnos_inscriptos(self, obj):
        return obj.inscripciones_carrera.activas().count()
    alumnos_inscriptos.short_description = _('Alumnos inscriptos')
    
    @admin.action(description=_('Activar carreras seleccionadas'))
    def activar_carreras(self, request, queryset):
        updated = queryset.update(activa=True)
        self.message_user(request, f"{updated} carreras activadas correctamente.")
    
    @admin.action(description=_('Desactivar carreras seleccionadas'))
    def desactivar_carreras(self, request, queryset):
        updated = queryset.update(activa=False)
        self.message_user(request, f"{updated} carreras desactivadas correctamente.")
    
    def has_delete_permission(self, request, obj=None):
        if obj and not obj.puede_eliminarse():
            return False
        return super().has_delete_permission(request, obj)


class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'carrera', 'docente', 'cupo_disponible', 'activa')
    list_filter = ('carrera', 'activa')
    search_fields = ('nombre', 'carrera__nombre', 'docente__apellido', 'docente__nombre')
    list_select_related = ('carrera', 'docente')
    raw_id_fields = ('docente',)
    actions = ['activar_materias', 'desactivar_materias']
    
    def cupo_disponible(self, obj):
        return f"{obj.inscripciones.activas().count()} / {obj.cupo_maximo}"
    cupo_disponible.short_description = _('Cupo')
    
    @admin.action(description=_('Activar materias seleccionadas'))
    def activar_materias(self, request, queryset):
        updated = queryset.update(activa=True)
        self.message_user(request, f"{updated} materias activadas correctamente.")
    
    @admin.action(description=_('Desactivar materias seleccionadas'))
    def desactivar_materias(self, request, queryset):
        updated = queryset.update(activa=False)
        self.message_user(request, f"{updated} materias desactivadas correctamente.")
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'docente':
            kwargs['queryset'] = Usuario.objects.filter(rol=Usuario.Rol.DOCENTE)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def has_delete_permission(self, request, obj=None):
        if obj and not obj.puede_eliminarse():
            return False
        return super().has_delete_permission(request, obj)


class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'materia', 'fecha_inscripcion', 'activa')
    list_filter = ('materia__carrera', 'activa')
    search_fields = (
        'alumno__dni', 'alumno__apellido', 'alumno__nombre',
        'materia__nombre', 'materia__carrera__nombre'
    )
    list_select_related = ('alumno', 'materia', 'materia__carrera')
    raw_id_fields = ('alumno', 'materia')
    date_hierarchy = 'fecha_inscripcion'
    actions = ['activar_inscripciones', 'desactivar_inscripciones']
    
    @admin.action(description=_('Activar inscripciones seleccionadas'))
    def activar_inscripciones(self, request, queryset):
        updated = queryset.update(activa=True)
        self.message_user(request, f"{updated} inscripciones activadas correctamente.")
    
    @admin.action(description=_('Desactivar inscripciones seleccionadas'))
    def desactivar_inscripciones(self, request, queryset):
        updated = queryset.update(activa=False)
        self.message_user(request, f"{updated} inscripciones desactivadas correctamente.")


class InscripcionCarreraAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'carrera', 'fecha_inscripcion', 'activa')
    list_filter = ('carrera', 'activa')
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
        updated = queryset.update(activa=True)
        self.message_user(request, f"{updated} inscripciones activadas correctamente.")
    
    @admin.action(description=_('Desactivar inscripciones seleccionadas'))
    def desactivar_inscripciones(self, request, queryset):
        updated = queryset.update(activa=False)
        self.message_user(request, f"{updated} inscripciones desactivadas correctamente.")


# Register models with their admin classes
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Carrera, CarreraAdmin)
admin.site.register(Materia, MateriaAdmin)
admin.site.register(Inscripcion, InscripcionAdmin)
admin.site.register(InscripcionCarrera, InscripcionCarreraAdmin)
