from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('manager', 'Hostel Manager'),
        ('admin', 'Administrator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(max_length=20, blank=True)
    student_number = models.CharField(max_length=20, blank=True)
    course = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    password_reset_token = models.UUIDField(null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_admin_user(self):
        return self.role == 'admin'


class Hostel(models.Model):
    name = models.CharField(max_length=200)
    # BUG FIX: manager should only be assigned to users with role='manager'
    manager = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_hostels',
        limit_choices_to={'role': 'manager'}
    )
    address = models.TextField()
    description = models.TextField()
    image = models.ImageField(upload_to='hostels/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def available_rooms_count(self):
        return self.rooms.filter(status='available').count()

    @property
    def total_rooms_count(self):
        return self.rooms.count()


class Room(models.Model):
    TYPE_CHOICES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('shared', 'Shared'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
    ]
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    price_per_semester = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('hostel', 'room_number')

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"


from datetime import date

def get_semester_choices():
    """Generate semester choices dynamically: current + next academic year."""
    today = date.today()
    start_year = today.year if today.month >= 8 else today.year - 1
    choices = []
    for year_offset in range(2):
        y = start_year + year_offset
        label1 = f"Semester 1 {y}/{y+1}"
        label2 = f"Semester 2 {y}/{y+1}"
        choices.append((label1, label1))
        choices.append((label2, label2))
    return choices

SEMESTER_CHOICES = get_semester_choices()


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    semester = models.CharField(max_length=50, choices=SEMESTER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    manager_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.room} ({self.status})"


class FeedbackMessage(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='feedback_messages')
    # BUG FIX: track which authenticated user sent the message (nullable for anonymous)
    sender = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_feedback'
    )
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.hostel.name}"


class MedicalRecord(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('Unknown', 'Unknown'),
    ]
    student = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='medical_record')
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, default='Unknown')
    known_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical Record - {self.student.get_full_name()}"
