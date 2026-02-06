from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Config
    path('config/new/', views.config_edit, name='config_new'),
    path('config/<int:pk>/', views.config_edit, name='config_edit'),
    path('config/<int:pk>/delete/', views.config_delete, name='config_delete'),

    # Dispatchers
    path('config/<int:config_pk>/dispatchers/', views.dispatchers, name='dispatchers'),
    path('dispatcher/<int:pk>/edit/', views.dispatcher_edit, name='dispatcher_edit'),
    path('dispatcher/<int:pk>/delete/', views.dispatcher_delete, name='dispatcher_delete'),
    path('dispatcher/<int:pk>/test/', views.dispatcher_test, name='dispatcher_test'),

    # Service control
    path('service/start/', views.service_start, name='service_start'),
    path('service/start/<int:config_pk>/', views.service_start_config, name='service_start_config'),
    path('service/stop/', views.service_stop, name='service_stop'),
    path('service/stop/<int:config_pk>/', views.service_stop_config, name='service_stop_config'),
    path('service/restart/', views.service_restart, name='service_restart'),
    path('service/restart/<int:config_pk>/', views.service_restart_config, name='service_restart_config'),
    path('api/status/', views.service_status, name='service_status'),
    path('api/config/<int:pk>/toggle-unmapped/', views.toggle_show_unmapped, name='toggle_show_unmapped'),
    path('logs/export/', views.export_logs, name='export_logs'),

    # Export / Import
    path('export/all/', views.export_all_configs, name='export_all_configs'),
    path('export/dispatchers/<int:config_pk>/', views.export_config_dispatchers, name='export_config_dispatchers'),
    path('import/configs/', views.import_configs, name='import_configs'),
    path('import/dispatchers/<int:config_pk>/', views.import_dispatchers, name='import_dispatchers'),
]
