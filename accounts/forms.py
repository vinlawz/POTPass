from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from core.models import Location

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Required. Enter your first name.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required. Enter your last name.')
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True, help_text='Select your role.')
    assigned_location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True), 
        required=True, 
        empty_label="Select a branch location",
        help_text='Required. Select the branch location for this user.'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'assigned_location', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize field labels and help texts
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters.'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
        # Add specific attributes for select fields
        if 'role' in self.fields:
            self.fields['role'].widget.attrs.update({'class': 'form-select'})
        if 'assigned_location' in self.fields:
            self.fields['assigned_location'].widget.attrs.update({'class': 'form-select'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with that username already exists. Please choose a different username.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        assigned_location = cleaned_data.get('assigned_location')
        
        # All users must have an assigned location
        if not assigned_location:
            raise forms.ValidationError('All users must be assigned to a branch location.')
        
        return cleaned_data

class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        
        # Add help texts
        self.fields['first_name'].help_text = 'Enter your first name'
        self.fields['last_name'].help_text = 'Enter your last name'
        self.fields['email'].help_text = 'Enter your email address'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is being changed and if it already exists for another user
        if email != self.instance.email:
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with that email already exists.')
        return email
