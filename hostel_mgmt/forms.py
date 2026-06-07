from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Hostel, Room, Booking, FeedbackMessage, MedicalRecord, SEMESTER_CHOICES


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    student_number = forms.CharField(max_length=20, required=True)
    course = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=20, required=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'student_number',
                  'course', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'course', 'student_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.TextInput(attrs={'class': 'form-control'}),
            'student_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class HostelForm(forms.ModelForm):
    # BUG FIX: admin can assign a manager when creating/editing a hostel
    manager = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='manager'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="— No manager assigned —",
    )

    class Meta:
        model = Hostel
        fields = ['name', 'address', 'description', 'image', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'price_per_semester', 'status', 'description']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'price_per_semester': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['semester']
        widgets = {
            'semester': forms.Select(attrs={'class': 'form-control'}),
        }


class FeedbackMessageForm(forms.ModelForm):
    """
    BUG FIX: when an authenticated student submits feedback, sender_name and
    sender_email are still shown for display but will be overridden in the view
    with the real user's data so no impersonation is possible.
    """
    class Meta:
        model = FeedbackMessage
        fields = ['sender_name', 'sender_email', 'subject', 'message']
        widgets = {
            'sender_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'sender_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your message...'}),
        }


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['blood_group', 'known_conditions', 'allergies', 'emergency_contact', 'emergency_phone']
        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'known_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List any known medical conditions...'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List any known allergies...'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact name'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+256 700 000000'}),
        }


class BookingDecisionForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['manager_note']
        widgets = {
            'manager_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional note to student...'}),
        }


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}))


class PasswordResetConfirmForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}), label='New Password')
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}), label='Confirm Password')

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class HostelSearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search hostels...'}))
    room_type = forms.ChoiceField(required=False, choices=[('', 'All Types'), ('single', 'Single'), ('double', 'Double'), ('shared', 'Shared')],
                                  widget=forms.Select(attrs={'class': 'form-control'}))
    max_price = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max price per semester'}))
