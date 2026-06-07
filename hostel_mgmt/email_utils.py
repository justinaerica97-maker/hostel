import requests
from django.conf import settings


def send_email(to_email, to_name, subject, html_content, text_content=None):
    """Send email via MailerSend HTTP API."""
    api_key = getattr(settings, 'MAILERSEND_API_KEY', None)
    if not api_key:
        print(f"\n[EMAIL SKIPPED - No API key]")
        print(f"To: {to_email}\nSubject: {subject}")
        print(f"Content: {text_content or html_content}\n")
        return False

    url = "https://api.mailersend.com/v1/email"
    headers = {
        "Authorization": f"Bearer {settings.MAILERSEND_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": {
            "email": settings.MAILERSEND_FROM_EMAIL,
            "name": settings.MAILERSEND_FROM_NAME,
        },
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "html": html_content,
        "text": text_content or subject,
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in (200, 202)
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False





def send_password_reset_email(user, request):
    token = user.password_reset_token
    reset_url = request.build_absolute_uri(f'/accounts/password-reset-confirm/{token}/')
    html = f"""
    <div style="font-family: sans-serif; max-width:600px; margin:auto;">
      <h2 style="color:#1a56db;">Reset Your Password</h2>
      <p>Hello {user.get_full_name() or user.username},</p>
      <p>We received a request to reset your password. Click the button below:</p>
      <a href="{reset_url}" style="display:inline-block;background:#1a56db;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;margin:16px 0;">Reset Password</a>
      <p>Or copy this link: <a href="{reset_url}">{reset_url}</a></p>
      <p><strong>This link expires in 1 hour.</strong></p>
      <p>If you did not request a password reset, please ignore this email.</p>
    </div>
    """
    return send_email(user.email, user.get_full_name() or user.username,
                      "Password Reset - Makerere Hostels", html)


def send_booking_approved_email(booking):
    user = booking.student
    html = f"""
    <div style="font-family: sans-serif; max-width:600px; margin:auto;">
      <h2 style="color:#057a55;">Booking Approved!</h2>
      <p>Hello {user.get_full_name() or user.username},</p>
      <p>Great news! Your booking request has been <strong>approved</strong>.</p>
      <table style="border-collapse:collapse; width:100%; margin:16px 0;">
        <tr><td style="padding:8px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Hostel</strong></td><td style="padding:8px; border:1px solid #e5e7eb;">{booking.room.hostel.name}</td></tr>
        <tr><td style="padding:8px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Room</strong></td><td style="padding:8px; border:1px solid #e5e7eb;">Room {booking.room.room_number} ({booking.room.get_room_type_display()})</td></tr>
        <tr><td style="padding:8px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Semester</strong></td><td style="padding:8px; border:1px solid #e5e7eb;">{booking.semester}</td></tr>
        <tr><td style="padding:8px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Price</strong></td><td style="padding:8px; border:1px solid #e5e7eb;">UGX {booking.room.price_per_semester:,.0f}/semester</td></tr>
      </table>
      {"<p><strong>Manager's Note:</strong> " + booking.manager_note + "</p>" if booking.manager_note else ""}
      <p>Please contact the hostel manager for further instructions on check-in.</p>
      <p>Congratulations!</p>
    </div>
    """
    return send_email(user.email, user.get_full_name() or user.username,
                      "Booking Approved - Makerere Hostels", html)


def send_booking_rejected_email(booking):
    user = booking.student
    html = f"""
    <div style="font-family: sans-serif; max-width:600px; margin:auto;">
      <h2 style="color:#c81e1e;">Booking Update</h2>
      <p>Hello {user.get_full_name() or user.username},</p>
      <p>We regret to inform you that your booking request has been <strong>rejected</strong>.</p>
      <table style="border-collapse:collapse; width:100%; margin:16px 0;">
        <tr><td style="padding:8px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Hostel</strong></td><td style="padding:8px; border:1px solid #e5e7eb;">{booking.room.hostel.name}</td></tr>
        <tr><td style="padding:8px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Room</strong></td><td style="padding:8px; border:1px solid #e5e7eb;">Room {booking.room.room_number}</td></tr>
        <tr><td style="padding:8px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Semester</strong></td><td style="padding:8px; border:1px solid #e5e7eb;">{booking.semester}</td></tr>
      </table>
      {"<p><strong>Reason:</strong> " + booking.manager_note + "</p>" if booking.manager_note else ""}
      <p>You may browse other available hostels and submit a new booking request.</p>
      <p>We apologise for any inconvenience.</p>
    </div>
    """
    return send_email(user.email, user.get_full_name() or user.username,
                      "Booking Status Update - Makerere Hostels", html)
