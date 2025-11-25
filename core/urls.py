from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'core'

urlpatterns = [
    # Home and Public
    path('', views.home, name='home'),
    path('carreras/', views.carreras, name='carreras'),
    path('carreras/inscribir/<int:carrera_id>/', views.inscribir_carrera, name='inscribir_carrera'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User
    path('perfil/', views.profile, name='perfil'),
    path('perfil/editar/', views.edit_profile, name='editar_perfil'),
    
    # Password Reset (using Django's built-in views)
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='core/auth/password_reset.html',
             email_template_name='core/auth/password_reset_email.html',
             subject_template_name='core/auth/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='core/auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='core/auth/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='core/auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Docente URLs
    path('dashboard/docente/', views.docente_dashboard, name='docente_dashboard'),
    path('dashboard/docente/mis-materias/', views.docente_mis_materias, name='docente_mis_materias'),
    path('dashboard/docente/materia/<int:materia_id>/', views.docente_detalle_materia, name='docente_detalle_materia'),
    path('dashboard/docente/materia/<int:materia_id>/asistencia/', views.tomar_asistencia, name='tomar_asistencia'),
    # REMEMBER. Attendance is a DOCENTE URL.
    
    # Alumno URLs
    path('dashboard/alumno/', views.alumno_dashboard, name='alumno_dashboard'),
    path('dashboard/alumno/mis-materias/', views.mis_materias, name='alumno_mis_materias'),
    path('dashboard/alumno/materia/<int:materia_id>/', views.detalle_materia, name='alumno_detalle_materia'),
    path('dashboard/alumno/inscripciones/', views.materias_inscripcion, name='materias_inscripcion'),
    
    # Preceptor URLs
    path('dashboard/preceptor/', views.preceptor_dashboard, name='preceptor_dashboard'),
    path('dashboard/preceptor/novedades/', views.novedades, name='novedades'),
    path('dashboard/preceptor/informe-inasistencias/', views.informe_inasistencias, name='informe_inasistencias'),
    path('dashboard/preceptor/alumno/<int:alumno_id>/', views.detalle_alumno, name='detalle_alumno'),
    path('dashboard/preceptor/alumno/<int:alumno_id>/notificar/', views.notificar_alumno, name='notificar_alumno'),
    path('dashboard/preceptor/', views.preceptor_dashboard, name='preceptor_dashboard'),
]

# Error Handlers
handler403 = 'core.views.handler403'
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
