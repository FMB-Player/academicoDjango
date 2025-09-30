# Sistema Académico

Sistema de gestión académica desarrollado con Django.

## Características

- Autenticación de usuarios con roles (Admin, Docente, Alumno, Preceptor)
- Dashboard personalizado por rol con estadísticas en tiempo real
- Manejo de errores personalizado (403, 404, 500)
- Interfaz responsiva con menú móvil
- Sistema de notificaciones integrado
- Estilos modulares con CSS moderno (CSS Variables, Flexbox, Grid)
- JavaScript modular para mejor mantenimiento
- Plantillas reutilizables y componentes UI consistentes

## Requisitos

### Producción
- Python 3.8+
- Django 5.0.x
- PostgreSQL (recomendado) o SQLite (desarrollo)

### Desarrollo
<!-- - Node.js (para compilar assets, opcional) -->
- Dependencias de desarrollo (ver `requirements-dev.txt`)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone [url-del-repositorio]
   cd academico
   ```

2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   # Instalar dependencias de producción
   pip install -r requirements.txt
   
   # Opcional: Para desarrollo, instalar dependencias adicionales
   pip install -r requirements-dev.txt
   ```

4. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. Aplicar migraciones:
   ```bash
   python manage.py migrate
   ```

6. Crear un superusuario:
   ```bash
   python manage.py createsuperuser
   ```

7. Iniciar el servidor de desarrollo:
   ```bash
   python manage.py runserver
   ```

## Estructura del Proyecto

```
academico/
├── core/                      # Aplicación principal
│   ├── migrations/            # Migraciones de la base de datos
│   ├── static/                # Archivos estáticos (CSS, JS, imágenes)
│   │   ├── core/
│   │   │   ├── css/          # Estilos CSS
│   │   │   ├── js/           # JavaScript
│   │   │   └── images/       # Imágenes
│   ├── templates/             # Plantillas HTML
│   │   ├── core/             # Plantillas de la aplicación core
│   │   │   ├── dashboards/   # Plantillas de dashboards
│   │   │   ├── errors/       # Plantillas de errores
│   │   │   └── ...
│   ├── templatetags/         # Etiquetas personalizadas
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── academico/                # Configuración del proyecto
├── manage.py
└── requirements.txt          # Dependencias
```

<!-- ## Personalización

### Estilos

Los estilos se encuentran en `core/static/core/css/`. Los principales archivos son:

- `style.css`: Estilos principales y variables CSS
- `dashboard.css`: Estilos específicos para los dashboards
  - Sistema de tarjetas y estadísticas
  - Componentes de interfaz reutilizables
  - Estados de interacción y hover
- `responsive.css`: Media queries para dispositivos móviles -->

### Estructura de Dashboards

- `base_dashboard.html`: Plantilla base común
- `admin/`: Vistas de administración
- `docente/`: Panel del docente
- `alumno/`: Panel del alumno
- `preceptor/`: Panel del preceptor

Cada dashboard incluye:
- Estadísticas rápidas
- Acciones principales
- Contenido específico por rol
- Diseño responsivo

<!-- ### JavaScript

El JavaScript principal está en `core/static/core/js/main.js` e incluye:

- Manejo del menú móvil
- Validación de formularios
- Notificaciones
- Comportamientos dinámicos -->

<!-- ## Despliegue

Para producción, configura las siguientes variables de entorno:

```
DEBUG=False
SECRET_KEY=tu-clave-secreta-segura
ALLOWED_HOSTS=.tudominio.com
``` -->

## Licencia

MIT
