from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('locations/', views.location_list_view, name='location_list'),
    path('locations/create/', views.location_create_view, name='location_create'),
    path('locations/<int:pk>/', views.location_detail_view, name='location_detail'),
    path('locations/<int:pk>/update/', views.location_update_view, name='location_update'),
    path('locations/<int:pk>/delete/', views.location_delete_view, name='location_delete'),
]
