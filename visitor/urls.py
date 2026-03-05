from django.urls import path
from . import views

app_name = 'visitor'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Check-in/Check-out
    path('check-in/', views.check_in_view, name='check_in'),
    path('check-out/<int:pk>/', views.check_out_view, name='check_out'),
    
    # Visitor Management
    path('visitors/', views.visitor_list_view, name='visitor_list'),
    path('visitors/register/', views.visitor_register_view, name='visitor_register'),
    path('visitors/create/', views.visitor_create_view, name='visitor_create'),
    
    # Visit Management
    path('visits/', views.visit_list_view, name='visit_list'),
    path('visits/create/<int:visitor_id>/', views.visit_create_view, name='visit_create'),
    path('visits/create/', views.visit_create_view, name='visit_create'),
    path('visits/<int:pk>/', views.visit_detail_view, name='visit_detail'),
    
    # Reports and Analytics
    path('reports/', views.reports_view, name='reports'),
    path('reports/export/', views.export_visits_view, name='export_visits'),
    path('reports/daily/', views.daily_summary_view, name='daily_summary'),
    path('reports/bulk-check-in/', views.bulk_check_in_view, name='bulk_check_in'),
    
    # AJAX
    path('search/', views.visitor_search_ajax, name='visitor_search_ajax'),
]
