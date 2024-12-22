from django.urls import path
from . import views
from .views import home

urlpatterns = [
    path('', home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('organizer_dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('attendees/<int:event_id>/', views.view_attendees, name='view_attendees'),
    path('attendee_dashboard/', views.attendee_dashboard, name='attendee_dashboard'),
    path('event/<int:event_id>/', views.event_details, name='event_details'),
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('refund_ticket/<int:ticket_id>/', views.refund_ticket, name='refund_ticket'),
    path('process-refund/<int:booking_id>/', views.process_refund, name='process_refund'),
    path('buy-ticket/<int:ticket_id>/', views.buy_ticket, name='buy_ticket'),
    path('payment-gateway/<int:booking_id>/', views.payment_gateway, name='payment_gateway'),
    path('confirm-payment/<int:booking_id>/', views.confirm_payment, name='confirm_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
]


