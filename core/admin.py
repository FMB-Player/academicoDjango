from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
# from django.contrib import messages
from django.contrib.auth.models import Group
# from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.views import redirect_to_login
from django.views.decorators.cache import never_cache
from .models import Usuario, Carrera, Materia, Inscripcion, InscripcionCarrera


class CustomUserCreationForm(forms.ModelForm):
    """Custom user creation form that doesn't require passwords for non-superusers."""
    
    class Meta:
        model = Usuario
        fields = ('email', 'dni', 'nombre', 'apellido', 'rol')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields['email'].required = True
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Set password to DNI
        if hasattr(user, 'dni') and user.dni:
            user.set_password(str(user.dni))
            user.debe_cambiar_password = True
        else:
            # Set a random password if no DNI
            import secrets
            temp_password = secrets.token_urlsafe(12)
            user.set_password(temp_password)
            user.debe_cambiar_password = True
        
        if commit:
            user.save()
        return user


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
        
        logout(request)
        return HttpResponseRedirect('/')


class UsuarioAdmin(UserAdmin):
    list_display = ('email', 'dni', 'nombre', 'apellido', 'rol', 'is_active')
    list_filter = ('rol', 'is_active')
    search_fields = ('email', 'dni', 'nombre', 'apellido')
    ordering = ('email', 'apellido', 'nombre')
    actions = ['reset_password_to_dni']
    change_form_template = 'admin/core/change_form.html'
    # change_list_template = 'admin/core/base_site.html'  # Temporarily disabled
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Use custom form for non-superusers creating users.
        """
        if not obj and not request.user.is_superuser:
            # For user creation by non-superusers, use our custom form
            kwargs['form'] = CustomUserCreationForm
        
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser:
            # Remove superuser and staff status from non-superusers
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'is_staff' in form.base_fields:
                form.base_fields['is_staff'].disabled = True
        
        return form
    
    fieldsets = (
        (None, {'fields': ('email',)}),
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
            'fields': ('email', 'dni', 'nombre', 'apellido', 'rol'),
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            # For new users, check if superuser to show password fields
            if request.user.is_superuser:
                return (
                    (None, {
                        'classes': ('wide',),
                        'fields': ('email', 'dni', 'nombre', 'apellido', 'password1', 'password2', 'rol'),
                    }),
                )
            else:
                return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    def save_model(self, request, obj, form, change):
        # For new users created by non-superusers, set password to DNI
        if not change and not request.user.is_superuser:
            if obj.dni:
                obj.set_password(str(obj.dni))
                obj.debe_cambiar_password = True
        super().save_model(request, obj, form, change)
    
    def response_change(self, request, obj):
        # Check if the reset password button was clicked
        if '_reset_password' in request.POST:
            # Set password to DNI and force change
            if obj.dni:
                obj.set_password(str(obj.dni))
                obj.debe_cambiar_password = True
                obj.save()
                self.message_user(request, f'Contraseña de {obj.email} reseteada a su DNI. Debe cambiarla en el próximo inicio de sesión.')
            return super().response_change(request, obj)
        
        return super().response_change(request, obj)
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:  # Only for existing objects
            extra_context['show_reset_password_button'] = True
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    @admin.action(description=_('Resetear contraseña a DNI'))
    def reset_password_to_dni(self, request, queryset):
        updated = 0
        for user in queryset:
            user.set_password(str(user.dni))
            user.debe_cambiar_password = True
            user.save()
            updated += 1
        self.message_user(request, f"{updated} usuarios han tenido su contraseña reseteada a su DNI y deben cambiarla.")
    reset_password_to_dni.short_description = _('Resetear contraseña a DNI')
    
    def delete_model(self, request, obj):
        """Override to perform logical deletion instead of actual deletion."""
        if request.user.is_superuser:
            # Superusers can actually delete
            super().delete_model(request, obj)
        else:
            # Regular users can only do logical deletion
            obj.is_active = False
            obj.save()
            from django.contrib import messages
            messages.info(request, 'Usuario desactivado (borrado lógico).')
    
    def delete_queryset(self, request, queryset):
        """Override to perform logical deletion for bulk actions."""
        if request.user.is_superuser:
            # Superusers can actually delete
            super().delete_queryset(request, queryset)
        else:
            # Regular users can only do logical deletion
            updated = queryset.filter(is_active=True).update(is_active=False)
            from django.contrib import messages
            messages.info(request, f'{updated} usuarios desactivados (borrado lógico).')


class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion', 'cupo_maximo', 'is_active', 'alumnos_inscriptos')
    list_filter = ('is_active',)
    search_fields = ('nombre',)
    actions = ['activar_carreras', 'desactivar_carreras']
    # change_list_template = 'admin/core/base_site.html'  # Temporarily disabled
    
    def alumnos_inscriptos(self, obj):
        return obj.inscripciones_carrera.activas().count()
    alumnos_inscriptos.short_description = _('Alumnos inscriptos')
    
    @admin.action(description=_('Activar carreras seleccionadas'))
    def activar_carreras(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} carreras activadas correctamente.")
    activar_carreras.short_description = _('Activar carreras seleccionadas')
    
    @admin.action(description=_('Desactivar carreras seleccionadas'))
    def desactivar_carreras(self, request, queryset):
        # Check if any have active enrollments
        carreras_con_inscripciones = queryset.filter(inscripciones_carrera__is_active=True)
        if carreras_con_inscripciones.exists():
            self.message_user(request, 
                f"No se pueden desactivar carreras con inscripciones activas: {', '.join([c.nombre for c in carreras_con_inscripciones])}", 
                level='ERROR')
            return
        
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} carreras desactivadas correctamente.")
    desactivar_carreras.short_description = _('Desactivar carreras seleccionadas')
    
    def has_delete_permission(self, request, obj=None):
        if obj and not obj.puede_eliminarse():
            return False
        return super().has_delete_permission(request, obj)
    
    def delete_model(self, request, obj):
        """Override to perform logical deletion instead of actual deletion."""
        if request.user.is_superuser:
            # Superusers can actually delete
            if obj.puede_eliminarse():
                super().delete_model(request, obj)
            else:
                from django.contrib import messages
                messages.error(request, 'No se puede eliminar este registro porque tiene datos asociados.')
        else:
            # Regular users can only do logical deletion
            if hasattr(obj, 'is_active'):
                obj.is_active = False
                obj.save()
                from django.contrib import messages
                messages.info(request, 'Registro desactivado (borrado lógico).')
            else:
                from django.contrib import messages
                messages.error(request, 'Este modelo no admite borrado lógico.')
    
    def delete_queryset(self, request, queryset):
        """Override to perform logical deletion for bulk actions."""
        if request.user.is_superuser:
            # Superusers can actually delete, but only if possible
            for obj in queryset:
                if not obj.puede_eliminarse():
                    from django.contrib import messages
                    messages.error(request, f'No se puede eliminar {obj} porque tiene datos asociados.')
                    return
            super().delete_queryset(request, queryset)
        else:
            # Regular users can only do logical deletion
            updated = queryset.filter(is_active=True).update(is_active=False)
            from django.contrib import messages
            messages.info(request, f'{updated} registros desactivados (borrado lógico).')


class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'mostrar_carreras', 'docente', 'cupo_disponible', 'is_active')
    list_filter = ('carreras', 'is_active')
    search_fields = ('nombre', 'carreras__nombre', 'docente__apellido', 'docente__nombre')
    filter_horizontal = ('carreras',)
    list_select_related = ('docente',)
    raw_id_fields = ('docente',)
    actions = ['activar_materias', 'desactivar_materias']
    # change_list_template = 'admin/core/base_site.html'  # Temporarily disabled
    
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
        # Check if any have active enrollments
        materias_con_inscripciones = queryset.filter(inscripciones__is_active=True)
        if materias_con_inscripciones.exists():
            self.message_user(request, 
                f"No se pueden desactivar materias con inscripciones activas: {', '.join([m.nombre for m in materias_con_inscripciones])}", 
                level='ERROR')
            return
        
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
    
    def delete_model(self, request, obj):
        """Override to perform logical deletion instead of actual deletion."""
        if request.user.is_superuser:
            # Superusers can actually delete
            if not obj.inscripciones.activas().exists():
                super().delete_model(request, obj)
            else:
                from django.contrib import messages
                messages.error(request, 'No se puede eliminar esta materia porque tiene inscripciones activas.')
        else:
            # Regular users can only do logical deletion
            obj.is_active = False
            obj.save()
            from django.contrib import messages
            messages.info(request, 'Materia desactivada (borrado lógico).')
    
    def delete_queryset(self, request, queryset):
        """Override to perform logical deletion for bulk actions."""
        if request.user.is_superuser:
            # Superusers can actually delete, but only if no active enrollments
            for obj in queryset:
                if obj.inscripciones.activas().exists():
                    from django.contrib import messages
                    messages.error(request, f'No se puede eliminar {obj} porque tiene inscripciones activas.')
                    return
            super().delete_queryset(request, queryset)
        else:
            # Regular users can only do logical deletion
            updated = queryset.filter(is_active=True).update(is_active=False)
            from django.contrib import messages
            messages.info(request, f'{updated} materias desactivadas (borrado lógico).')


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
    # change_list_template = 'admin/core/base_site.html'  # Temporarily disabled
    
    def carreras_materia(self, obj):
        return ", ".join([c.nombre for c in obj.materia.carreras.all()])
    carreras_materia.short_description = _('Carreras')
    
    @admin.action(description=_('Activar inscripciones seleccionadas'))
    def activar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} inscripciones activadas correctamente.")
    activar_inscripciones.short_description = _('Activar inscripciones seleccionadas')
    
    @admin.action(description=_('Desactivar inscripciones seleccionadas'))
    def desactivar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} inscripciones desactivadas correctamente.")
    desactivar_inscripciones.short_description = _('Desactivar inscripciones seleccionadas')
    
    def delete_model(self, request, obj):
        """Override to perform logical deletion instead of actual deletion."""
        if request.user.is_superuser:
            # Superusers can actually delete
            super().delete_model(request, obj)
        else:
            # Regular users can only do logical deletion
            obj.is_active = False
            obj.save()
            from django.contrib import messages
            messages.info(request, 'Inscripción desactivada (borrado lógico).')
    
    def delete_queryset(self, request, queryset):
        """Override to perform logical deletion for bulk actions."""
        if request.user.is_superuser:
            # Superusers can actually delete
            super().delete_queryset(request, queryset)
        else:
            # Regular users can only do logical deletion
            updated = queryset.filter(is_active=True).update(is_active=False)
            from django.contrib import messages
            messages.info(request, f'{updated} inscripciones desactivadas (borrado lógico).')


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
    # change_list_template = 'admin/core/base_site.html'  # Temporarily disabled
    
    @admin.action(description=_('Activar inscripciones seleccionadas'))
    def activar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} inscripciones activadas correctamente.")
    activar_inscripciones.short_description = _('Activar inscripciones seleccionadas')
    
    @admin.action(description=_('Desactivar inscripciones seleccionadas'))
    def desactivar_inscripciones(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} inscripciones desactivadas correctamente.")
    desactivar_inscripciones.short_description = _('Desactivar inscripciones seleccionadas')
    
    def delete_model(self, request, obj):
        """Override to perform logical deletion instead of actual deletion."""
        if request.user.is_superuser:
            # Superusers can actually delete
            super().delete_model(request, obj)
        else:
            # Regular users can only do logical deletion
            obj.is_active = False
            obj.save()
            from django.contrib import messages
            messages.info(request, 'Inscripción a carrera desactivada (borrado lógico).')
    
    def delete_queryset(self, request, queryset):
        """Override to perform logical deletion for bulk actions."""
        if request.user.is_superuser:
            # Superusers can actually delete
            super().delete_queryset(request, queryset)
        else:
            # Regular users can only do logical deletion
            updated = queryset.filter(is_active=True).update(is_active=False)
            from django.contrib import messages
            messages.info(request, f'{updated} inscripciones a carrera desactivadas (borrado lógico).')


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
