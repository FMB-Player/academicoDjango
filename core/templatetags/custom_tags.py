"""
This module provides backward compatibility for templates that use 'custom_tags'.
All functionality has been moved to core_tags.py.
"""
from .core_tags import *  # noqa
from django import template
import random
import string

register = template.Library()

@register.filter
def mask_email(email):
    """
    Masks the local part of an email address, keeping the first few characters visible
    and replacing the rest with '*', then reattaching the domain.

    Examples:
      johndoe@gmail.com -> joh****@gmail.com
      ab@gmail.com -> ab@gmail.com  (no masking if too short)
    """
    if not email or '@' not in email:
        return email

    local, domain = email.split('@', 1)

    # Adjust this if you want more or fewer visible characters
    visible_prefix_len = 3

    # Only mask if the local part is longer than the visible prefix
    if len(local) > visible_prefix_len:
        masked_len = len(local) - visible_prefix_len
        masked_local = f"{local[:visible_prefix_len]}{'*' * masked_len}"
    else:
        masked_local = local  # too short to mask

    return f"{masked_local}@{domain}"

def fake_code(length:int):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))