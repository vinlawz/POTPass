from django import forms
from .models import Location

class LocationForm(forms.ModelForm):
    """Form for creating and updating locations"""
    
    class Meta:
        model = Location
        fields = ('name', 'code', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter branch name (e.g., Swahilipot Hub)',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter branch code (e.g., HUB)',
                'required': True,
                'style': 'text-transform: uppercase;'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        self.fields['is_active'].required = False
        
        # Add help texts
        self.fields['name'].help_text = 'Required. Enter the full name of this branch.'
        self.fields['code'].help_text = 'Required. Enter a unique code (max 10 characters).'
        self.fields['is_active'].help_text = 'Whether this branch is currently active.'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Check if name is being changed and if it already exists for another location
        if self.instance.pk:
            # Updating existing location
            if Location.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('A location with this name already exists.')
        else:
            # Creating new location
            if Location.objects.filter(name=name).exists():
                raise forms.ValidationError('A location with this name already exists.')
        return name

    def clean_code(self):
        code = self.cleaned_data.get('code')
        # Convert to uppercase
        code = code.upper() if code else code
        
        # Check if code is being changed and if it already exists for another location
        if self.instance.pk:
            # Updating existing location
            if Location.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('A location with this code already exists.')
        else:
            # Creating new location
            if Location.objects.filter(code=code).exists():
                raise forms.ValidationError('A location with this code already exists.')
        return code
