from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import AnonymousUser
from .models import AuditLog

@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    """Log all model changes for audit trail"""
    # Only log for specific models that need auditing
    audit_models = ['Visitor', 'Visit']
    
    if sender.__name__ in audit_models:
        action = 'CREATE' if created else 'UPDATE'
        
        # Determine the object type
        if sender.__name__ == 'Visitor':
            visitor = instance
            AuditLog.objects.create(
                user=None,  # System action
                action=f'CREATE_VISITOR' if created else 'UPDATE_VISITOR',
                visitor=visitor,
                notes=f'Visitor {visitor.full_name} {"created" if created else "updated"}'
            )
        elif sender.__name__ == 'Visit':
            visit = instance
            user = visit.created_by
            AuditLog.objects.create(
                user=user,
                action=f'CHECK_IN' if created else 'UPDATE_VISIT',
                visit=visit,
                visitor=visit.visitor,
                notes=f'Visit for {visit.visitor.full_name} {"created" if created else "updated"}'
            )

def get_client_ip(request):
    """Helper function to get client IP address"""
    if request is None:
        return None
    
    # Try to get IP from various headers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip
