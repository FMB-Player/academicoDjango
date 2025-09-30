"""
Custom template tags and filters for the core app.
"""
from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def active_page(request, view_name):
    """
    Returns 'active' if the current page matches the given view name.
    Usage: {% active_page request 'view_name' %}
    """
    if not request:
        return ''
    
    # Get the current path without leading slash
    current_path = request.path.strip('/')
    # Get the view name path (might be a partial match for nested URLs)
    view_path = view_name.strip('/')
    
    # Check for exact match or if the current path starts with the view path
    if current_path == view_path or current_path.startswith(view_path + '/'):
        return 'active'
    return ''

@register.filter
def has_role(user, roles):
    """
    Check if the user has any of the specified roles.
    Usage: {% if user|has_role:"ADMIN,PRECEPTOR" %}
    """
    if not user.is_authenticated:
        return False
    
    # Convert comma-separated roles to a list
    role_list = [r.strip().upper() for r in roles.split(',')]
    return user.rol in role_list

@register.simple_tag
def get_setting(name, default=''):
    """
    Get a setting from Django's settings, with an optional default value.
    Usage: {% get_setting 'SITE_NAME' 'Default Site' %}
    """
    return getattr(settings, name, default)

@register.filter
def add_class(field, css_class):
    """
    Add a CSS class to a form field.
    Usage: {{ field|add_class:"form-control" }}
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget') and hasattr(field.field.widget, 'attrs'):
        field.field.widget.attrs['class'] = field.field.widget.attrs.get('class', '') + ' ' + css_class
    return field
