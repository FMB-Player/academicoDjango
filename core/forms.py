from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class ProfileEditForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        ),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['nombre', 'apellido', 'email', 'telefono', 'direccion', 'fecha_nacimiento']
        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej: +54 9 11 1234-5678'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email readonly since it's used as username
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['email'].help_text = 'Para cambiar el correo electrónico, contacte al administrador.'
        
        # Add Bootstrap classes to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class CustomPasswordChangeForm(BasePasswordChangeForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
