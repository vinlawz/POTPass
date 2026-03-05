from django import forms
from django.core.exceptions import ValidationError
from .models import Visitor, Visit
from django.utils import timezone

class VisitorForm(forms.ModelForm):
    """Form for creating and updating visitors"""
    
    class Meta:
        model = Visitor
        fields = ['full_name', 'phone', 'id_number', 'organization', 'email', 'gender', 'date_of_birth', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name',
                'autofocus': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
                'pattern': r'[0-9+()-\s]+',
                'title': 'Enter phone number with country code'
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ID number (optional)'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter organization (optional)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address (optional)'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address (optional)'
            }),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError('Phone number is required.')
        
        # Remove common formatting characters for validation
        clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        if len(clean_phone) < 10:
            raise ValidationError('Phone number must be at least 10 digits.')
        
        return phone
    
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name or len(full_name.strip()) < 2:
            raise ValidationError('Full name must be at least 2 characters long.')
        return full_name.strip()

class VisitForm(forms.ModelForm):
    """Form for creating and updating visits"""
    
    class Meta:
        model = Visit
        fields = ['visitor', 'purpose', 'host', 'host_department', 'notes']
        widgets = {
            'visitor': forms.Select(attrs={
                'class': 'form-select',
                'data-live-search': 'true'
            }),
            'purpose': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter purpose of visit',
                'required': True
            }),
            'host': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter host name (optional)'
            }),
            'host_department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        location = kwargs.pop('location', None)
        super().__init__(*args, **kwargs)
        
        # Filter visitors by location
        if location:
            self.fields['visitor'].queryset = Visitor.objects.filter(
                visits__location=location
            ).distinct() or Visitor.objects.none()

class VisitorSearchForm(forms.Form):
    """Form for searching visitors"""
    
    SEARCH_TYPE_CHOICES = [
        ('name', 'By Name'),
        ('phone', 'By Phone'),
        ('id_number', 'By ID Number'),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPE_CHOICES,
        initial='phone',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search visitors...',
            'autofocus': True
        })
    )

class VisitFilterForm(forms.Form):
    """Form for filtering visit records"""
    
    STATUS_CHOICES = [('', 'All Status')] + Visit.STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default dates to today and this month
        from django.utils import timezone
        today = timezone.now().date()
        self.fields['date_from'].initial = today.replace(day=1)
        self.fields['date_to'].initial = today

class CheckInForm(forms.Form):
    """Form for quick check-in"""
    
    search_query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by phone or ID...',
            'autofocus': True,
            'id': 'checkin-search'
        })
    )
    
    def clean_search_query(self):
        query = self.cleaned_data.get('search_query', '').strip()
        if not query:
            raise ValidationError('Please enter a phone number or ID to search.')
        return query

class CheckOutForm(forms.Form):
    """Form for visitor check-out confirmation"""
    
    confirm = forms.BooleanField(
        label='I confirm this visitor is checking out',
        required=True,
        widget=forms.Checkbox(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Check-out notes (optional)'
        })
    )
