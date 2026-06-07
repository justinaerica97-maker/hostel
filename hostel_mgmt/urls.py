from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Auth
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/password-reset/', views.password_reset_request, name='password_reset_request'),
    path('accounts/password-reset-confirm/<uuid:token>/', views.password_reset_confirm, name='password_reset_confirm'),

    # Profile
    path('accounts/profile/', views.profile_view, name='profile'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Hostels
    path('hostels/', views.hostel_list, name='hostel_list'),
    path('hostels/<int:pk>/', views.hostel_detail, name='hostel_detail'),

    # Booking
    path('bookings/book/<int:room_id>/', views.book_room, name='book_room'),
    path('bookings/my/', views.my_bookings, name='my_bookings'),
    path('bookings/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),

    # Manager: bookings
    path('manager/bookings/', views.manage_bookings, name='manage_bookings'),
    path('manager/bookings/<int:booking_id>/approve/', views.approve_booking, name='approve_booking'),
    path('manager/bookings/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),

    # Manager: hostels & rooms
    path('manager/hostels/', views.manage_hostels, name='manage_hostels'),
    path('manager/hostels/create/', views.create_hostel, name='create_hostel'),
    path('manager/hostels/<int:pk>/edit/', views.edit_hostel, name='edit_hostel'),
    path('manager/hostels/<int:hostel_id>/rooms/', views.manage_rooms, name='manage_rooms'),
    path('manager/hostels/<int:hostel_id>/rooms/add/', views.add_room, name='add_room'),
    path('manager/rooms/<int:room_id>/edit/', views.edit_room, name='edit_room'),

    # Feedback
    path('manager/feedback/', views.view_feedback, name='view_feedback'),
    path('manager/feedback/<int:msg_id>/read/', views.mark_feedback_read, name='mark_feedback_read'),

    # Medical
    path('medical/my-record/', views.my_medical_record, name='my_medical_record'),
    path('admin-panel/medical-records/', views.admin_medical_records, name='admin_medical_records'),

    # Admin
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:user_id>/change-role/', views.admin_change_user_role, name='admin_change_user_role'),
]
