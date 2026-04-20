from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.my_tickets, name='my_tickets'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:ticket_id>/edit/', views.edit_ticket, name='edit'),
    path('<int:ticket_id>/comment/', views.add_comment, name='add_comment'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    # path('api/assign/', views.api_assign_tickets, name='api_assign_tickets'),
    # path('api/delete/', views.api_delete_tickets, name='api_delete_tickets'),

    # path('notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]
