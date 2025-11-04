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
   cd [nombre-del-repositorio]
   ```

2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   "venv\Scripts\activate"  # En Linux: venv/bin/activate
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
   ```
   Mientras sigas el formato dado, puedes cambiar todas las variables a tu gusto. Esto es importante si quieres usar el entorno de debug. El default si no haces este paso irá directamente a "producción"

5. Aplicar migraciones:
   ```bash
   python manage.py migrate
   ```

6. Crear un superusuario:
   ```bash
   python manage.py createsuperuser
   ```
   Sigue las instrucciones y crea UN superusuario. Los otros usuarios NO tendrán los mismos permisos que el superusuario y deben ser configurados, puedes ver más a detalle deswde el admin panel una vez que actives el servidor.

7. Iniciar el servidor:
   ```bash
   python manage.py runserver
   ```

## Estructura del Proyecto

```
academico/
├── academico/                # Configuración del proyecto
|   ├── settings.py           # Configuración
|   └── ...
├── core/                      # Aplicación principal
│   ├── migrations/            # Migraciones de la base de datos
│   ├── static/                # Archivos estáticos (CSS, JS, imágenes)
│   │   └── core/
│   │       ├── css/          # Estilos CSS
│   │       └── js/           # JavaScript
│   ├── templates/            # Plantillas HTML
│   │   └── core/             # Plantillas de la aplicación core
|   |       ├── auth          # Formularios y detalles
│   │       ├── dashboards/   # Plantillas de dashboards
│   │       ├── errors/       # Plantillas de errores
|   |       └── ...
│   ├── templatetags/         # Etiquetas personalizadas
|   ├── tests/                # Testing
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
|   └── ...
├── manage.py
├── requirements-dev.txt      # Dependencias del entorno de desarrollo
├── requirements.txt          # Dependencias
└── ...
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

## Gestión de Archivos Estáticos

### Estructura de Directorios

- `core/static/core/`: Contiene los archivos estáticos personalizados (CSS, JS, imágenes).
  - `css/`: Hojas de estilo personalizadas
  - `js/`: Scripts JavaScript personalizados
  - `images/`: Imágenes y recursos gráficos

### Desarrollo

En desarrollo, Django sirve automáticamente los archivos estáticos cuando `DJANGO_DEBUG=True`.

### Producción

En producción, corre el siguiente código antes de activar el servidor:
   ```bash
   python manage.py collectstatic
   ```
   Esto copiará todos los archivos estáticos al directorio `STATIC_ROOT` (por defecto `staticfiles/`) y permitirá usar los recursos especializados.
   Finalmente, cambia la variable de .env a cualquier cosa que no sea `True` (o por extensión deja vacío) para poder iniciar el servidor en producción. Esto obviamente evitará que ante errores se muestre el monitor de debuggeo.

## Licencia

MIT
