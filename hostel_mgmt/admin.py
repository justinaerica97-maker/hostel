from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Hostel, Room, Booking, FeedbackMessage, MedicalRecord


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'date_joined']
    list_filter = ['role']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'student_number', 'course', 'profile_picture')}),
    )


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'address', 'is_active', 'available_rooms_count']
    list_filter = ['is_active']
    search_fields = ['name', 'address']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'hostel', 'room_type', 'price_per_semester', 'status']
    list_filter = ['room_type', 'status']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['student', 'room', 'semester', 'status', 'created_at']
    list_filter = ['status', 'semester']
    search_fields = ['student__username', 'room__room_number']


@admin.register(FeedbackMessage)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['subject', 'hostel', 'sender_name', 'is_read', 'created_at']
    list_filter = ['is_read']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'blood_group', 'updated_at']
    search_fields = ['student__username', 'student__first_name']
