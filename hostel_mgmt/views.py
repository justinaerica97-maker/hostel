from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse, Http404
import uuid
from datetime import timedelta

from .models import CustomUser, Hostel, Room, Booking, FeedbackMessage, MedicalRecord
from .forms import (StudentRegistrationForm, ProfileUpdateForm, HostelForm, RoomForm,
                    BookingForm, FeedbackMessageForm, MedicalRecordForm, BookingDecisionForm,
                    PasswordResetRequestForm, PasswordResetConfirmForm, HostelSearchForm)
from .email_utils import (send_password_reset_email,
                           send_booking_approved_email, send_booking_rejected_email)
from .decorators import student_required, manager_required, admin_required, login_and_verified_required


# ─── Home ────────────────────────────────────────────────────────────────────
def home(request):
    hostels = Hostel.objects.filter(is_active=True)[:6]
    return render(request, 'home.html', {'hostels': hostels})


# ─── Auth ─────────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        logout(request)
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                user.password_reset_token = uuid.uuid4()
                user.password_reset_expires = timezone.now() + timedelta(hours=1)
                user.save()
                send_password_reset_email(user, request)
            except CustomUser.DoesNotExist:
                pass
            messages.success(request, "If that email exists in our system, a reset link has been sent.")
            return redirect('login')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'registration/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    try:
        user = CustomUser.objects.get(password_reset_token=token)
        if user.password_reset_expires < timezone.now():
            messages.error(request, "This reset link has expired. Please request a new one.")
            return redirect('password_reset_request')
    except CustomUser.DoesNotExist:
        messages.error(request, "Invalid reset link.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.password_reset_token = None
            user.password_reset_expires = None
            user.save()
            messages.success(request, "Password reset successfully. You can now log in.")
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()
    return render(request, 'registration/password_reset_confirm.html', {'form': form})


# ─── Dashboard ────────────────────────────────────────────────────────────────
@login_and_verified_required
def dashboard(request):
    user = request.user
    if user.role == 'admin':
        ctx = {
            'total_students': CustomUser.objects.filter(role='student').count(),
            'total_hostels': Hostel.objects.count(),
            'total_rooms': Room.objects.count(),
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'unread_feedback': FeedbackMessage.objects.filter(is_read=False).count(),
            'recent_bookings': Booking.objects.select_related('student', 'room__hostel').order_by('-created_at')[:10],
            'all_users': CustomUser.objects.all().order_by('-date_joined')[:10],
        }
        return render(request, 'dashboard/admin_dashboard.html', ctx)

    elif user.role == 'manager':
        hostels = Hostel.objects.filter(manager=user)
        pending_bookings = Booking.objects.filter(
            room__hostel__in=hostels, status='pending'
        ).select_related('student', 'room__hostel')
        ctx = {
            'hostels': hostels,
            'pending_bookings': pending_bookings,
            'total_rooms': Room.objects.filter(hostel__in=hostels).count(),
            'approved_bookings': Booking.objects.filter(room__hostel__in=hostels, status='approved').count(),
        }
        return render(request, 'dashboard/manager_dashboard.html', ctx)

    else:  # student
        bookings = Booking.objects.filter(student=user).select_related('room__hostel').order_by('-created_at')
        ctx = {
            'bookings': bookings,
            'active_booking': bookings.filter(status='approved').first(),
        }
        return render(request, 'dashboard/student_dashboard.html', ctx)


# ─── Profile ──────────────────────────────────────────────────────────────────
@login_and_verified_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


# ─── Hostel Listings ──────────────────────────────────────────────────────────
def hostel_list(request):
    form = HostelSearchForm(request.GET)
    hostels = Hostel.objects.filter(is_active=True).prefetch_related('rooms')

    q = request.GET.get('q', '')
    room_type = request.GET.get('room_type', '')
    max_price = request.GET.get('max_price', '')

    if q:
        hostels = hostels.filter(Q(name__icontains=q) | Q(address__icontains=q) | Q(description__icontains=q))
    if room_type:
        hostels = hostels.filter(rooms__room_type=room_type).distinct()
    if max_price:
        try:
            hostels = hostels.filter(rooms__price_per_semester__lte=float(max_price)).distinct()
        except ValueError:
            pass

    return render(request, 'hostels/hostel_list.html', {'hostels': hostels, 'form': form, 'q': q})


def hostel_detail(request, pk):
    hostel = get_object_or_404(Hostel, pk=pk, is_active=True)
    rooms = hostel.rooms.all()

    # BUG FIX: pre-populate form with authenticated student's info so the
    # message is FROM the student, not asking them to type their own name.
    initial = {}
    if request.user.is_authenticated and request.user.role == 'student':
        initial = {
            'sender_name': request.user.get_full_name() or request.user.username,
            'sender_email': request.user.email,
        }
    feedback_form = FeedbackMessageForm(initial=initial)

    has_active_booking = False
    if request.user.is_authenticated and request.user.role == 'student':
        has_active_booking = Booking.objects.filter(
            student=request.user,
            status__in=['pending', 'approved']
        ).exists()

    if request.method == 'POST' and 'feedback_submit' in request.POST:
        feedback_form = FeedbackMessageForm(request.POST)
        if feedback_form.is_valid():
            msg = feedback_form.save(commit=False)
            msg.hostel = hostel
            # BUG FIX: link message to the authenticated user if they are logged in
            if request.user.is_authenticated:
                msg.sender = request.user
                # BUG FIX: override sender_name/email with the real user's info
                # so a student cannot impersonate someone else
                msg.sender_name = request.user.get_full_name() or request.user.username
                msg.sender_email = request.user.email
            msg.save()
            messages.success(request, "Your message has been sent!")
            return redirect('hostel_detail', pk=pk)

    return render(request, 'hostels/hostel_detail.html', {
        'hostel': hostel, 'rooms': rooms, 'feedback_form': feedback_form,
        'has_active_booking': has_active_booking
    })


# ─── Booking ──────────────────────────────────────────────────────────────────
@login_and_verified_required
@student_required
def book_room(request, room_id):
    # BUG FIX: also check room belongs to an active hostel
    room = get_object_or_404(Room, pk=room_id, status='available', hostel__is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            semester = form.cleaned_data['semester']
            # Check if student already has a pending or approved booking for this semester
            existing = Booking.objects.filter(
                student=request.user,
                semester=semester,
                status__in=['pending', 'approved']
            ).first()

            if existing:
                messages.warning(request, f"You already have an active or pending booking for {semester}.")
                return redirect('my_bookings')

            # BUG FIX: re-check room is still available at save time (race condition guard)
            room.refresh_from_db()
            if room.status != 'available':
                messages.error(request, "Sorry, that room is no longer available.")
                return redirect('hostel_detail', pk=room.hostel.pk)

            booking = form.save(commit=False)
            booking.student = request.user
            booking.room = room
            booking.status = 'pending'
            booking.save()
            messages.success(request, "Booking request submitted! The manager will review it shortly.")
            return redirect('my_bookings')
    else:
        form = BookingForm()
    return render(request, 'bookings/book_room.html', {'room': room, 'form': form})


@login_and_verified_required
@student_required
def my_bookings(request):
    bookings = Booking.objects.filter(student=request.user).select_related('room__hostel').order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_and_verified_required
@student_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, student=request.user, status__in=['pending', 'approved'])
    if request.method == 'POST':
        if booking.status == 'approved':
            room = booking.room
            room.status = 'available'
            room.save()
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, "Your booking has been cancelled and the room has been freed.")
        else:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, "Booking request cancelled successfully.")
    return redirect('my_bookings')


# ─── Manager: Booking Decisions ───────────────────────────────────────────────
@login_and_verified_required
@manager_required
def manage_bookings(request):
    if request.user.role == 'admin':
        bookings = Booking.objects.select_related('student', 'room__hostel').order_by('-created_at')
    else:
        # BUG FIX: manager only sees bookings for their own hostels
        hostels = Hostel.objects.filter(manager=request.user)
        bookings = Booking.objects.filter(
            room__hostel__in=hostels
        ).select_related('student', 'room__hostel').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'bookings/manage_bookings.html', {'bookings': bookings, 'status_filter': status_filter})


@login_and_verified_required
@manager_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    # Guard: if already processed, redirect with a clear message instead of 404
    if booking.status != 'pending':
        status_label = booking.get_status_display()
        messages.warning(request, f"This booking has already been {status_label.lower()} and cannot be approved again.")
        return redirect('manage_bookings')

    # Enforce ownership for manager role (admin can approve any)
    if request.user.role == 'manager':
        if booking.room.hostel.manager != request.user:
            messages.error(request, "You don't manage this hostel.")
            return redirect('manage_bookings')

    # Block approval if room is already occupied by a different approved booking
    other_approved = Booking.objects.filter(
        room=booking.room, status='approved'
    ).exclude(pk=booking.pk).exists()
    if other_approved:
        messages.error(request, "This room already has an approved booking.")
        return redirect('manage_bookings')

    if request.method == 'POST':
        form = BookingDecisionForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.status = 'approved'
            booking.room.status = 'occupied'
            booking.room.save()
            booking.save()
            # Reject other pending bookings for the same room
            Booking.objects.filter(
                room=booking.room, status='pending'
            ).exclude(pk=booking.pk).update(status='rejected')
            send_booking_approved_email(booking)
            messages.success(request, "Booking approved and student notified.")
            return redirect('manage_bookings')
    else:
        form = BookingDecisionForm(instance=booking)
    return render(request, 'bookings/booking_decision.html', {'booking': booking, 'form': form, 'action': 'approve'})


@login_and_verified_required
@manager_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    # Guard: if already processed, redirect with a clear message instead of 404
    if booking.status != 'pending':
        status_label = booking.get_status_display()
        messages.warning(request, f"This booking has already been {status_label.lower()} and cannot be rejected again.")
        return redirect('manage_bookings')

    # Enforce ownership for manager role
    if request.user.role == 'manager':
        if booking.room.hostel.manager != request.user:
            messages.error(request, "You don't manage this hostel.")
            return redirect('manage_bookings')

    if request.method == 'POST':
        form = BookingDecisionForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.status = 'rejected'
            booking.save()
            # Free the room only if no other approved booking holds it
            if booking.room.status == 'occupied':
                other_approved = Booking.objects.filter(
                    room=booking.room, status='approved'
                ).exclude(pk=booking.pk).exists()
                if not other_approved:
                    booking.room.status = 'available'
                    booking.room.save()
            send_booking_rejected_email(booking)
            messages.success(request, "Booking rejected and student notified.")
            return redirect('manage_bookings')
    else:
        form = BookingDecisionForm(instance=booking)
    return render(request, 'bookings/booking_decision.html', {'booking': booking, 'form': form, 'action': 'reject'})


# ─── Manager: Hostels & Rooms ─────────────────────────────────────────────────
@login_and_verified_required
@manager_required
def manage_hostels(request):
    if request.user.role == 'admin':
        hostels = Hostel.objects.all().prefetch_related('rooms')
    else:
        hostels = Hostel.objects.filter(manager=request.user).prefetch_related('rooms')
    return render(request, 'hostels/manage_hostels.html', {'hostels': hostels})


@login_and_verified_required
@manager_required
def create_hostel(request):
    # BUG FIX: only admin can create hostels (managers are assigned by admin)
    if request.user.role != 'admin':
        messages.error(request, "Only administrators can create new hostels.")
        return redirect('manage_hostels')
    if request.method == 'POST':
        form = HostelForm(request.POST, request.FILES)
        if form.is_valid():
            hostel = form.save(commit=False)
            hostel.save()
            messages.success(request, "Hostel created successfully!")
            return redirect('manage_hostels')
    else:
        form = HostelForm()
    return render(request, 'hostels/hostel_form.html', {'form': form, 'title': 'Add New Hostel'})


@login_and_verified_required
@manager_required
def edit_hostel(request, pk):
    hostel = get_object_or_404(Hostel, pk=pk)
    if request.user.role == 'manager' and hostel.manager != request.user:
        messages.error(request, "You don't have permission to edit this hostel.")
        return redirect('manage_hostels')
    if request.method == 'POST':
        form = HostelForm(request.POST, request.FILES, instance=hostel)
        if form.is_valid():
            form.save()
            messages.success(request, "Hostel updated successfully!")
            return redirect('manage_hostels')
    else:
        form = HostelForm(instance=hostel)
    return render(request, 'hostels/hostel_form.html', {'form': form, 'hostel': hostel, 'title': 'Edit Hostel'})


@login_and_verified_required
@manager_required
def manage_rooms(request, hostel_id):
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    if request.user.role == 'manager' and hostel.manager != request.user:
        messages.error(request, "You don't manage this hostel.")
        return redirect('manage_hostels')
    rooms = hostel.rooms.all()
    return render(request, 'hostels/manage_rooms.html', {'hostel': hostel, 'rooms': rooms})


@login_and_verified_required
@manager_required
def add_room(request, hostel_id):
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    if request.user.role == 'manager' and hostel.manager != request.user:
        messages.error(request, "You don't manage this hostel.")
        return redirect('manage_hostels')
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.hostel = hostel
            room.save()
            messages.success(request, f"Room {room.room_number} added!")
            return redirect('manage_rooms', hostel_id=hostel_id)
    else:
        form = RoomForm()
    return render(request, 'hostels/room_form.html', {'form': form, 'hostel': hostel, 'title': 'Add Room'})


@login_and_verified_required
@manager_required
def edit_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if request.user.role == 'manager' and room.hostel.manager != request.user:
        messages.error(request, "You don't manage this room's hostel.")
        return redirect('manage_hostels')
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Room updated!")
            return redirect('manage_rooms', hostel_id=room.hostel.pk)
    else:
        form = RoomForm(instance=room)
    return render(request, 'hostels/room_form.html', {'form': form, 'room': room, 'hostel': room.hostel, 'title': 'Edit Room'})


# ─── Feedback ─────────────────────────────────────────────────────────────────
@login_and_verified_required
@manager_required
def view_feedback(request):
    if request.user.role == 'admin':
        messages_qs = FeedbackMessage.objects.select_related('hostel', 'sender').order_by('-created_at')
    else:
        # BUG FIX: manager only sees messages for their own hostels
        hostels = Hostel.objects.filter(manager=request.user)
        messages_qs = FeedbackMessage.objects.filter(
            hostel__in=hostels
        ).select_related('hostel', 'sender').order_by('-created_at')
    return render(request, 'feedback/feedback_list.html', {'messages': messages_qs})


@login_and_verified_required
@manager_required
def mark_feedback_read(request, msg_id):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('view_feedback')
    msg = get_object_or_404(FeedbackMessage, pk=msg_id)

    # BUG FIX: manager must own the hostel that received this message
    if request.user.role == 'manager':
        if msg.hostel.manager != request.user:
            messages.error(request, "You don't have permission to manage this message.")
            return redirect('view_feedback')

    msg.is_read = True
    msg.save()
    messages.success(request, "Message marked as read.")
    return redirect('view_feedback')


# ─── Medical Records ──────────────────────────────────────────────────────────
@login_and_verified_required
@student_required
def my_medical_record(request):
    record, created = MedicalRecord.objects.get_or_create(student=request.user)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            saved_record = form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Medical record updated successfully!',
                    'last_updated': saved_record.updated_at.strftime("%d %b %Y, %H:%M")
                })
            messages.success(request, "Medical record updated!")
            return redirect('my_medical_record')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()
                }, status=400)
    else:
        form = MedicalRecordForm(instance=record)
    return render(request, 'medical/my_medical_record.html', {'form': form, 'record': record})


@login_and_verified_required
@admin_required
def admin_medical_records(request):
    records = MedicalRecord.objects.select_related('student').order_by('student__last_name')
    q = request.GET.get('q', '')
    if q:
        records = records.filter(
            Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) |
            Q(student__student_number__icontains=q)
        )
    return render(request, 'medical/admin_medical_records.html', {'records': records, 'q': q})


# ─── Admin: User Management ───────────────────────────────────────────────────
@login_and_verified_required
@admin_required
def admin_users(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/admin_users.html', {'users': users})


@login_and_verified_required
@admin_required
def admin_change_user_role(request, user_id):
    """BUG FIX: admin was missing the ability to change user roles via the UI."""
    if request.method != 'POST':
        return redirect('admin_users')
    target_user = get_object_or_404(CustomUser, pk=user_id)
    new_role = request.POST.get('role', '')
    valid_roles = [r[0] for r in CustomUser.ROLE_CHOICES]
    if new_role not in valid_roles:
        messages.error(request, "Invalid role specified.")
        return redirect('admin_users')
    # Prevent admin from demoting themselves
    if target_user == request.user and new_role != 'admin':
        messages.error(request, "You cannot change your own admin role.")
        return redirect('admin_users')
    old_role = target_user.role
    target_user.role = new_role
    target_user.save()
    messages.success(request, f"{target_user.get_full_name() or target_user.username} role changed from {old_role} to {new_role}.")
    return redirect('admin_users')
