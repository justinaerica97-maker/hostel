from django.core.management.base import BaseCommand
from hostel_mgmt.models import CustomUser, Hostel, Room


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **kwargs):
        # Admin
        if not CustomUser.objects.filter(username='admin').exists():
            admin = CustomUser.objects.create_superuser(
                username='admin', email='admin@makerere.ac.ug',
                password='Admin@1234', role='admin',
                first_name='System', last_name='Administrator'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / Admin@1234'))

        # Manager
        if not CustomUser.objects.filter(username='manager1').exists():
            manager = CustomUser.objects.create_user(
                username='manager1', email='manager@example.com',
                password='Manager@1234', role='manager',
                first_name='James', last_name='Manager', phone_number='+256700000001'
            )
        else:
            manager = CustomUser.objects.get(username='manager1')

        # Student
        if not CustomUser.objects.filter(username='student1').exists():
            CustomUser.objects.create_user(
                username='student1', email='student@example.com',
                password='Student@1234', role='student',
                first_name='Jane', last_name='Student',
                student_number='21/U/00001', course='BSc Computer Science',
                phone_number='+256700000002'
            )
            self.stdout.write(self.style.SUCCESS('Created student: student1 / Student@1234'))

        # Hostels
        if not Hostel.objects.exists():
            hostel1 = Hostel.objects.create(
                name='Makerere View Hostel',
                manager=manager,
                address='Plot 12, University Road, Kampala',
                description='A modern and comfortable hostel located just 5 minutes walk from Makerere University main gate. We offer clean, secure, and affordable accommodation for students.',
                is_active=True
            )
            hostel2 = Hostel.objects.create(
                name='Campus Edge Residence',
                manager=manager,
                address='Plot 45, Bombo Road, Kampala',
                description='Premium student accommodation with high-speed internet, 24/7 security, and a common study area. Close to all university facilities.',
                is_active=True
            )

            # Rooms for hostel 1
            for i in range(1, 6):
                Room.objects.create(
                    hostel=hostel1, room_number=f'A{i:02d}',
                    room_type='single', price_per_semester=850000,
                    status='available' if i <= 3 else 'occupied',
                    description='Spacious single room with study desk, wardrobe, and window.'
                )
            for i in range(1, 4):
                Room.objects.create(
                    hostel=hostel1, room_number=f'B{i:02d}',
                    room_type='shared', price_per_semester=500000,
                    status='available',
                    description='Shared room for two students. Includes bunk beds and shared storage.'
                )

            # Rooms for hostel 2
            for i in range(1, 4):
                Room.objects.create(
                    hostel=hostel2, room_number=f'101{i}',
                    room_type='double', price_per_semester=1200000,
                    status='available',
                    description='Deluxe double room with en-suite bathroom, AC, and fast WiFi.'
                )
            for i in range(1, 3):
                Room.objects.create(
                    hostel=hostel2, room_number=f'201{i}',
                    room_type='single', price_per_semester=950000,
                    status='available',
                    description='Single room with private bathroom and kitchenette.'
                )

            self.stdout.write(self.style.SUCCESS('Created 2 sample hostels with rooms'))

        self.stdout.write(self.style.SUCCESS('\n=== Sample Data Created ==='))
        self.stdout.write('Admin:   admin / Admin@1234')
        self.stdout.write('Manager: manager1 / Manager@1234')
        self.stdout.write('Student: student1 / Student@1234')
