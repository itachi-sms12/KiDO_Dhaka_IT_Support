from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('tickets/', views.all_tickets, name='all_tickets'),
    path('tickets/<int:ticket_id>/assign/', views.assign_ticket, name='assign_ticket'),
    path('tickets/<int:ticket_id>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/add/', views.add_user, name='add_user'),
    path('categories/', views.manage_categories, name='manage_categories'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.export_report, name='export_report'),
    path('assign/', views.assign_tickets, name='assign_tickets'),
    path('delete/', views.delete_tickets, name='delete_tickets'),
    # path('tickets/assign/api/', views.assign_ticket_api, name='assign_ticket_api'),
    path('api/tickets/assign/', views.api_assign_tickets, name='api_assign_tickets'),
    path('api/tickets/delete/', views.api_delete_tickets, name='api_delete_tickets'),
    path('api/staff-search/', views.staff_search, name='staff_search'),
    path('users/toggle/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),
    path('users/role/<int:user_id>/', views.change_user_role, name='change_user_role'),
    path('users/edit/<int:user_id>/', views.get_user_details, name='get_user_details'),
    path('get_user_details/<int:user_id>/', views.get_user_details, name='get_user_details'),
    path('update_user_details/<int:user_id>/', views.update_user_details, name='update_user_details'),
    path('export-report/', views.export_report, name='export_report'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),






]
