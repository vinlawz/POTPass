from django.urls import path
from . import views

app_name = 'reception'

urlpatterns = [
    path('passes/', views.pass_list_view, name='pass_list'),
    path('passes/create/', views.pass_create_view, name='pass_create'),
    path('passes/<int:pk>/', views.pass_detail_view, name='pass_detail'),
    path('passes/<int:pk>/update/', views.pass_update_view, name='pass_update'),
    path('passes/<int:pk>/checkout/', views.pass_checkout_view, name='pass_checkout'),
]
