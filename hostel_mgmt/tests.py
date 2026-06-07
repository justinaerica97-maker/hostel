from django.test import TestCase, Client
from django.urls import reverse
from hostel_mgmt.models import CustomUser, Hostel, Room, Booking, FeedbackMessage, MedicalRecord, get_semester_choices

class HostelSystemTests(TestCase):
    def setUp(self):
        # Create users
        self.client = Client()
        
        self.admin = CustomUser.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='AdminPassword123',
            role='admin'
        )
        
        self.manager = CustomUser.objects.create_user(
            username='testmanager',
            email='manager@test.com',
            password='ManagerPassword123',
            role='manager'
        )
        
        self.student = CustomUser.objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='StudentPassword123',
            role='student'
        )
        
        # Create a hostel
        self.hostel = Hostel.objects.create(
            name='Test Hostel',
            manager=self.manager,
            address='123 Test St, Kampala',
            description='Comfortable test accommodation.',
            is_active=True
        )
        
        # Create rooms
        self.room_available = Room.objects.create(
            hostel=self.hostel,
            room_number='101',
            room_type='single',
            price_per_semester=800000,
            status='available',
            description='Single test room'
        )
        
        self.room_occupied = Room.objects.create(
            hostel=self.hostel,
            room_number='102',
            room_type='single',
            price_per_semester=800000,
            status='occupied',
            description='Occupied test room'
        )

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Hostel')

    def test_hostel_list(self):
        response = self.client.get(reverse('hostel_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Hostel')

    def test_hostel_detail(self):
        response = self.client.get(reverse('hostel_detail', args=[self.hostel.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Hostel')
        self.assertContains(response, 'Room 101')

    def test_student_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        # Should redirect to login since not authenticated
        self.assertEqual(response.status_code, 302)

    def test_student_dashboard_authenticated(self):
        self.client.login(username='teststudent', password='StudentPassword123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back')

    def test_booking_workflow(self):
        # 1. Login student
        self.client.login(username='teststudent', password='StudentPassword123')
        
        # 2. Book an available room
        booking_url = reverse('book_room', args=[self.room_available.pk])
        response = self.client.post(booking_url, {
            'semester': get_semester_choices()[0][0]  # Use first valid dynamic semester
        })
        self.assertEqual(response.status_code, 302) # Redirect to my_bookings
        
        # Check booking exists and is pending
        booking = Booking.objects.get(student=self.student, room=self.room_available)
        self.assertEqual(booking.status, 'pending')
        
        # 3. Log out student, log in manager
        self.client.logout()
        self.client.login(username='testmanager', password='ManagerPassword123')
        
        # 4. Approve the booking
        approve_url = reverse('approve_booking', args=[booking.pk])
        response = self.client.post(approve_url, {
            'manager_note': 'Approved for test'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify status transitions
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'approved')
        
        self.room_available.refresh_from_db()
        self.assertEqual(self.room_available.status, 'occupied')

    def test_submit_feedback(self):
        url = reverse('hostel_detail', args=[self.hostel.pk])
        response = self.client.post(url, {
            'feedback_submit': True,
            'sender_name': 'Feedback User',
            'sender_email': 'feedback@test.com',
            'subject': 'Test Subject',
            'message': 'This is a test message.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FeedbackMessage.objects.filter(subject='Test Subject').exists())

    def test_admin_medical_records_requires_admin(self):
        self.client.login(username='teststudent', password='StudentPassword123')
        response = self.client.get(reverse('admin_medical_records'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_admin_medical_records_as_admin(self):
        self.client.login(username='testadmin', password='AdminPassword123')
        response = self.client.get(reverse('admin_medical_records'))
        self.assertEqual(response.status_code, 200)

    def test_student_can_view_medical_record_form(self):
        self.client.login(username='teststudent', password='StudentPassword123')
        response = self.client.get(reverse('my_medical_record'))
        self.assertEqual(response.status_code, 200)

    def test_student_save_medical_record_ajax(self):
        self.client.login(username='teststudent', password='StudentPassword123')
        response = self.client.post(
            reverse('my_medical_record'),
            {
                'blood_group': 'O+',
                'known_conditions': 'None',
                'allergies': 'Peanuts',
                'emergency_contact': 'Parent Name',
                'emergency_phone': '+256700000003'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode('utf-8'),
            {
                'success': True,
                'message': 'Medical record updated successfully!',
                'last_updated': response.json()['last_updated']
            }
        )
        # Verify db updated
        record = MedicalRecord.objects.get(student=self.student)
        self.assertEqual(record.blood_group, 'O+')
        self.assertEqual(record.allergies, 'Peanuts')


