"""
populate_demo.py
----------------
Wipes the entire database and creates a rich, realistic demo dataset covering
every feature of the Makerere Hostel Management System:

  • 1 admin
  • 4 hostel managers (each assigned to a hostel)
  • 20 students across different courses/years
  • 4 hostels with varied rooms (single/double/shared, available/occupied/maintenance)
  • Bookings in every status: pending, approved, rejected, cancelled
  • Room statuses updated consistently with approved bookings
  • Medical records for all students (varied blood groups / conditions)
  • Feedback messages (read and unread, linked to authenticated students)

Usage:
    python manage.py populate_demo
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import random

from hostel_mgmt.models import (
    CustomUser, Hostel, Room, Booking,
    FeedbackMessage, MedicalRecord, get_semester_choices
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def wipe():
    """Delete all app data in dependency order, reset sequences."""
    MedicalRecord.objects.all().delete()
    FeedbackMessage.objects.all().delete()
    Booking.objects.all().delete()
    Room.objects.all().delete()
    Hostel.objects.all().delete()
    CustomUser.objects.all().delete()

    # Reset SQLite auto-increment counters
    tables = [
        'hostel_mgmt_medicalrecord', 'hostel_mgmt_feedbackmessage',
        'hostel_mgmt_booking', 'hostel_mgmt_room', 'hostel_mgmt_hostel',
        'hostel_mgmt_customuser', 'auth_user',
    ]
    with connection.cursor() as cur:
        for t in tables:
            try:
                cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}';")
            except Exception:
                pass


SEMESTERS = [s[0] for s in get_semester_choices()]

COURSES = [
    'BSc Computer Science',
    'BSc Information Technology',
    'Bachelor of Commerce',
    'BSc Civil Engineering',
    'Bachelor of Laws (LLB)',
    'BSc Electrical Engineering',
    'Bachelor of Education',
    'BSc Statistics',
    'Bachelor of Arts (Economics)',
    'BSc Biomedical Engineering',
]

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown']

CONDITIONS = [
    '',
    'Asthma (mild, managed with inhaler)',
    'Type 2 Diabetes (diet-controlled)',
    'Hypertension (on medication)',
    'Epilepsy (well-controlled)',
    '',
    'Sickle cell trait',
    '',
    'Chronic sinusitis',
    '',
]

ALLERGIES = [
    '',
    'Penicillin',
    'Peanuts and tree nuts',
    'Dust mites',
    'Latex',
    '',
    'Sulfa drugs',
    'Shellfish',
    '',
    'Pollen (seasonal)',
]

FEEDBACK_SUBJECTS = [
    ('Water supply issue in Block B', 'The water supply in Block B has been inconsistent for the past week. We often have no water from 6 AM to 10 AM which makes morning routines very difficult. Please look into this urgently.'),
    ('Request for extra study desks', 'As exams are approaching, we would appreciate additional study desks in the common room. Currently there are only 4 desks for over 20 students on this floor.'),
    ('Broken window latch in room 104', 'The window latch in room 104 has been broken for two weeks now. This is a security concern especially at night. Could maintenance please attend to it?'),
    ('WiFi connectivity problems', 'The WiFi router on the 3rd floor frequently drops connection between 8 PM and midnight, which is exactly when most students are studying. Please check the router or add another access point.'),
    ('Appreciation for clean facilities', 'I just wanted to write in to appreciate the cleaning staff. The hostel has been very clean lately and we really value the effort. Thank you to the management for maintaining these standards.'),
    ('Noise complaint — ground floor corridor', 'There is excessive noise in the ground floor corridor every evening after 10 PM. Some residents are playing music loudly. Could management please enforce the quiet hours policy?'),
    ('Request for laundry area extension', 'The current laundry area can only accommodate 6 students at a time. With 40+ residents, queues are very long on weekends. Could additional drying lines be installed outside?'),
    ('Parking space request', 'Several of us have motorcycles and there is currently no designated parking. Our bikes are being parked in the corridor which is a fire hazard. Can management allocate a parking area?'),
    ('Inquiry about semester 2 availability', 'I am a second year student looking to book a room for Semester 2. Could you let me know what room types are available and whether I need to apply early? Thank you.'),
    ('Faulty bathroom door lock — room 207', 'The bathroom door lock in room 207 does not engage properly. This is an urgent privacy and safety issue. Please send maintenance as soon as possible.'),
    ('Generator fuel request', 'During last week\'s power outage, the generator ran out of fuel after only 2 hours. Please ensure adequate fuel is always available, especially during exam periods.'),
    ('Thank you for quick maintenance response', 'I reported a leaking pipe on Monday and it was fixed by Tuesday morning. I am really impressed by the quick response. Keep up the good work!'),
]

MANAGER_NOTES_APPROVE = [
    'Welcome to the hostel! Please collect your key from the office between 8 AM and 5 PM on weekdays.',
    'Booking approved. Kindly bring your student ID and one passport photo when checking in.',
    'Your room is ready. Please review the hostel rules document available at reception.',
    'Approved. Note that check-in is between Monday and Friday only. Contact us to arrange weekend check-in.',
    'Booking confirmed. Please pay the semester fee at the bursar\'s office and bring the receipt on arrival.',
]

MANAGER_NOTES_REJECT = [
    'Sorry, this room has already been allocated to another student. Please apply for a different room.',
    'Your booking could not be approved at this time as we are awaiting verification of your student status. Please contact the Dean of Students office.',
    'Rejected — the room you requested is currently under maintenance. Please select an available room and re-apply.',
    'We are unable to process this booking as the student already has an active booking for this semester.',
    'Room reserved for continuing students. New students are eligible to book from the second week of semester.',
]


class Command(BaseCommand):
    help = 'Wipe database and populate with rich demo data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('⚠  Wiping entire database...'))
        wipe()
        self.stdout.write(self.style.SUCCESS('✓  Database wiped\n'))

        # ── 1. ADMIN ──────────────────────────────────────────────────────────
        admin = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@makerere.ac.ug',
            password='Admin@1234',
            first_name='Dorothy',
            last_name='Nakato',
            role='admin',
            phone_number='+256772000001',
        )
        self.stdout.write(self.style.SUCCESS('✓  Admin created'))

        # ── 2. MANAGERS ───────────────────────────────────────────────────────
        managers_data = [
            ('manager1', 'James',    'Ochieng',   'james.ochieng@makerere.ac.ug',   '+256772100001'),
            ('manager2', 'Patricia', 'Namukasa',  'p.namukasa@makerere.ac.ug',       '+256772100002'),
            ('manager3', 'Robert',   'Ssemakula', 'r.ssemakula@makerere.ac.ug',      '+256772100003'),
            ('manager4', 'Grace',    'Atim',      'g.atim@makerere.ac.ug',           '+256772100004'),
        ]
        managers = []
        for uname, fname, lname, email, phone in managers_data:
            m = CustomUser.objects.create_user(
                username=uname, email=email, password='Manager@1234',
                first_name=fname, last_name=lname,
                role='manager', phone_number=phone,
            )
            managers.append(m)
        self.stdout.write(self.style.SUCCESS(f'✓  {len(managers)} managers created'))

        # ── 3. HOSTELS ────────────────────────────────────────────────────────
        hostels_data = [
            {
                'name': 'Makerere View Hostel',
                'manager': managers[0],
                'address': 'Plot 12, University Road, Kampala',
                'description': (
                    'Makerere View Hostel is a modern, purpose-built student residence located just '
                    '5 minutes walk from the main university gate. We offer clean, secure, and '
                    'affordable accommodation in a quiet, study-friendly environment.\n\n'
                    'Facilities include 24/7 security, high-speed WiFi, a spacious common room, '
                    'laundry area, and regular cleaning services. All rooms have large windows, '
                    'study desks, wardrobes, and reliable electricity with backup generator.'
                ),
                'is_active': True,
            },
            {
                'name': 'Campus Edge Residence',
                'manager': managers[1],
                'address': 'Plot 45, Bombo Road, Kampala',
                'description': (
                    'Campus Edge Residence is a premium student accommodation facility offering '
                    'comfortable, modern rooms with high-speed fibre internet. Situated on Bombo Road, '
                    'it provides easy access to Makerere University, Mulago Hospital, and the city centre.\n\n'
                    'Amenities include a fully equipped study lounge, rooftop terrace, CCTV surveillance, '
                    'biometric access control, and an on-site caretaker available around the clock. '
                    'We take pride in maintaining a clean, safe, and conducive living environment.'
                ),
                'is_active': True,
            },
            {
                'name': 'Freedom Hall Annex',
                'manager': managers[2],
                'address': 'Plot 7, Wandegeya, Kampala',
                'description': (
                    'Freedom Hall Annex is a well-established student hostel in the heart of Wandegeya, '
                    'one of Kampala\'s most vibrant student neighbourhoods. It offers a range of room '
                    'types to suit different budgets, from affordable shared rooms to comfortable singles.\n\n'
                    'The hostel is minutes from Makerere University, with numerous restaurants, '
                    'pharmacies, and convenience stores nearby. Features include a common kitchen, '
                    'secure storage, guest parking, and a resident warden.'
                ),
                'is_active': True,
            },
            {
                'name': 'Nile Crest Student Lodge',
                'manager': managers[3],
                'address': 'Plot 3, Kikoni, Kampala',
                'description': (
                    'Nile Crest Student Lodge is a newly constructed hostel in the quiet Kikoni '
                    'neighbourhood, offering premium en-suite double rooms and standard single rooms. '
                    'Designed with the modern student in mind, every room features tiled floors, '
                    'built-in wardrobes, and high-quality furniture.\n\n'
                    'The lodge offers fibre internet, a dedicated study hall open 24 hours, '
                    'a small gym, and a secure parking lot. Management is responsive and committed '
                    'to maintaining the highest standards of student welfare.'
                ),
                'is_active': True,
            },
        ]

        hostels = []
        for hd in hostels_data:
            h = Hostel.objects.create(**hd)
            hostels.append(h)
        self.stdout.write(self.style.SUCCESS(f'✓  {len(hostels)} hostels created'))

        # ── 4. ROOMS ──────────────────────────────────────────────────────────
        # hostel[0] — Makerere View: mix of singles and shared
        rooms_h0 = []
        single_descs = [
            'Spacious single room with study desk, wardrobe, ceiling fan, and large window overlooking the courtyard.',
            'Compact single room ideal for focused study. Includes desk, bookshelf, wardrobe, and bedside lamp.',
            'Corner single room with extra natural light. Furnished with study desk, chair, wardrobe, and single bed.',
        ]
        for i in range(1, 9):
            status = 'available'
            if i in (3, 6):
                status = 'occupied'
            if i == 8:
                status = 'maintenance'
            rooms_h0.append(Room.objects.create(
                hostel=hostels[0], room_number=f'A{i:02d}',
                room_type='single', price_per_semester=850000,
                status=status,
                description=single_descs[i % 3],
            ))
        for i in range(1, 5):
            status = 'available' if i <= 3 else 'occupied'
            rooms_h0.append(Room.objects.create(
                hostel=hostels[0], room_number=f'B{i:02d}',
                room_type='shared', price_per_semester=480000,
                status=status,
                description='Shared room for two students. Features bunk beds, individual lockable storage, shared study desk, and a window.',
            ))

        # hostel[1] — Campus Edge: doubles and singles, premium pricing
        rooms_h1 = []
        for i in range(1, 7):
            status = 'available'
            if i in (2, 5):
                status = 'occupied'
            rooms_h1.append(Room.objects.create(
                hostel=hostels[1], room_number=f'D{i:02d}',
                room_type='double', price_per_semester=1350000,
                status=status,
                description='Deluxe double room with en-suite bathroom, air conditioning, 43" smart TV mount, fibre WiFi, and premium furnishings.',
            ))
        for i in range(1, 5):
            status = 'available' if i != 3 else 'maintenance'
            rooms_h1.append(Room.objects.create(
                hostel=hostels[1], room_number=f'S{i:02d}',
                room_type='single', price_per_semester=980000,
                status=status,
                description='Premium single room with private bathroom, kitchenette, high-speed WiFi, and a dedicated study area.',
            ))

        # hostel[2] — Freedom Hall: budget-friendly mixed
        rooms_h2 = []
        for i in range(1, 6):
            status = 'available' if i <= 4 else 'occupied'
            rooms_h2.append(Room.objects.create(
                hostel=hostels[2], room_number=f'101{i}',
                room_type='shared', price_per_semester=380000,
                status=status,
                description='Affordable shared room for three students. Equipped with three single beds, a shared wardrobe, and a study table.',
            ))
        for i in range(1, 4):
            rooms_h2.append(Room.objects.create(
                hostel=hostels[2], room_number=f'201{i}',
                room_type='single', price_per_semester=620000,
                status='available',
                description='Standard single room with study desk, wardrobe, ceiling fan, and window. Quiet floor.',
            ))
        Room.objects.create(
            hostel=hostels[2], room_number='301A',
            room_type='double', price_per_semester=900000,
            status='maintenance',
            description='Double room currently under renovation. Expected to be available next semester.',
        )

        # hostel[3] — Nile Crest: new, premium
        rooms_h3 = []
        for i in range(1, 5):
            status = 'available' if i != 2 else 'occupied'
            rooms_h3.append(Room.objects.create(
                hostel=hostels[3], room_number=f'NC10{i}',
                room_type='double', price_per_semester=1500000,
                status=status,
                description='Brand new en-suite double room. Features marble tiles, built-in wardrobe, smart desk lamp, fibre internet, and blackout curtains.',
            ))
        for i in range(1, 7):
            status = 'available'
            if i in (3, 6):
                status = 'occupied'
            rooms_h3.append(Room.objects.create(
                hostel=hostels[3], room_number=f'NC20{i}',
                room_type='single', price_per_semester=1100000,
                status=status,
                description='Modern single room with tiled floor, built-in storage, ergonomic desk chair, and high-speed WiFi. 24-hour gym access included.',
            ))

        total_rooms = Room.objects.count()
        self.stdout.write(self.style.SUCCESS(f'✓  {total_rooms} rooms created across 4 hostels'))

        # ── 5. STUDENTS ───────────────────────────────────────────────────────
        students_data = [
            # (username, first, last, email, student_no, course, phone, year)
            ('nakato_s',   'Aisha',      'Nakato',    'a.nakato@students.mak.ac.ug',    '21/U/00101', COURSES[0], '+256700100001', 3),
            ('opio_b',     'Brian',      'Opio',      'b.opio@students.mak.ac.ug',       '22/U/00102', COURSES[1], '+256700100002', 2),
            ('namirembe_c','Christine',  'Namirembe', 'c.namirembe@students.mak.ac.ug',  '20/U/00103', COURSES[2], '+256700100003', 4),
            ('ssali_d',    'David',      'Ssali',     'd.ssali@students.mak.ac.ug',      '23/U/00104', COURSES[3], '+256700100004', 1),
            ('akello_e',   'Esther',     'Akello',    'e.akello@students.mak.ac.ug',     '21/U/00105', COURSES[4], '+256700100005', 3),
            ('mugisha_f',  'Frank',      'Mugisha',   'f.mugisha@students.mak.ac.ug',    '22/U/00106', COURSES[5], '+256700100006', 2),
            ('nambi_g',    'Gloria',     'Nambi',     'g.nambi@students.mak.ac.ug',      '23/U/00107', COURSES[6], '+256700100007', 1),
            ('okello_h',   'Henry',      'Okello',    'h.okello@students.mak.ac.ug',     '20/U/00108', COURSES[7], '+256700100008', 4),
            ('aciro_i',    'Irene',      'Aciro',     'i.aciro@students.mak.ac.ug',      '21/U/00109', COURSES[8], '+256700100009', 3),
            ('wasswa_j',   'John',       'Wasswa',    'j.wasswa@students.mak.ac.ug',     '22/U/00110', COURSES[9], '+256700100010', 2),
            ('nakabugo_k', 'Karen',      'Nakabugo',  'k.nakabugo@students.mak.ac.ug',   '23/U/00111', COURSES[0], '+256700100011', 1),
            ('lubega_l',   'Lawrence',   'Lubega',    'l.lubega@students.mak.ac.ug',     '20/U/00112', COURSES[1], '+256700100012', 4),
            ('namusisi_m', 'Martha',     'Namusisi',  'm.namusisi@students.mak.ac.ug',   '21/U/00113', COURSES[2], '+256700100013', 3),
            ('oryem_n',    'Nathan',     'Oryem',     'n.oryem@students.mak.ac.ug',      '22/U/00114', COURSES[3], '+256700100014', 2),
            ('atuhaire_o', 'Olivia',     'Atuhaire',  'o.atuhaire@students.mak.ac.ug',   '23/U/00115', COURSES[4], '+256700100015', 1),
            ('kiggundu_p', 'Patrick',    'Kiggundu',  'p.kiggundu@students.mak.ac.ug',   '20/U/00116', COURSES[5], '+256700100016', 4),
            ('nansubuga_q','Queen',      'Nansubuga', 'q.nansubuga@students.mak.ac.ug',  '21/U/00117', COURSES[6], '+256700100017', 3),
            ('tumwebaze_r','Ronald',     'Tumwebaze', 'r.tumwebaze@students.mak.ac.ug',  '22/U/00118', COURSES[7], '+256700100018', 2),
            ('namukasa_s', 'Sandra',     'Namukasa',  's.namukasa@students.mak.ac.ug',   '23/U/00119', COURSES[8], '+256700100019', 1),
            ('byarugaba_t','Timothy',    'Byarugaba', 't.byarugaba@students.mak.ac.ug',  '20/U/00120', COURSES[9], '+256700100020', 4),
        ]

        students = []
        for uname, fname, lname, email, sno, course, phone, year in students_data:
            s = CustomUser.objects.create_user(
                username=uname, email=email, password='Student@1234',
                first_name=fname, last_name=lname,
                role='student', student_number=sno,
                course=course, phone_number=phone,
            )
            students.append(s)
        self.stdout.write(self.style.SUCCESS(f'✓  {len(students)} students created'))

        # ── 6. MEDICAL RECORDS ────────────────────────────────────────────────
        emergency_contacts = [
            ('Margaret Nakato',   '+256772200001'),
            ('Peter Opio',        '+256772200002'),
            ('Joseph Namirembe',  '+256772200003'),
            ('Ruth Ssali',        '+256772200004'),
            ('Moses Akello',      '+256772200005'),
            ('Alice Mugisha',     '+256772200006'),
            ('Paul Nambi',        '+256772200007'),
            ('Grace Okello',      '+256772200008'),
            ('Charles Aciro',     '+256772200009'),
            ('Florence Wasswa',   '+256772200010'),
            ('David Nakabugo',    '+256772200011'),
            ('Sarah Lubega',      '+256772200012'),
            ('Emmanuel Namusisi', '+256772200013'),
            ('Lydia Oryem',       '+256772200014'),
            ('Simon Atuhaire',    '+256772200015'),
            ('Mary Kiggundu',     '+256772200016'),
            ('Isaac Nansubuga',   '+256772200017'),
            ('Deborah Tumwebaze', '+256772200018'),
            ('Stephen Namukasa',  '+256772200019'),
            ('Hannah Byarugaba',  '+256772200020'),
        ]
        for i, student in enumerate(students):
            ec_name, ec_phone = emergency_contacts[i]
            MedicalRecord.objects.create(
                student=student,
                blood_group=BLOOD_GROUPS[i % len(BLOOD_GROUPS)],
                known_conditions=CONDITIONS[i % len(CONDITIONS)],
                allergies=ALLERGIES[i % len(ALLERGIES)],
                emergency_contact=ec_name,
                emergency_phone=ec_phone,
            )
        self.stdout.write(self.style.SUCCESS(f'✓  Medical records created for all {len(students)} students'))

        # ── 7. BOOKINGS ───────────────────────────────────────────────────────
        sem1 = SEMESTERS[0]  # e.g. "Semester 1 2025/2026"
        sem2 = SEMESTERS[1]  # e.g. "Semester 2 2025/2026"
        sem3 = SEMESTERS[2] if len(SEMESTERS) > 2 else sem1

        bookings_spec = [
            # (student_idx, room, semester, status, manager_note)
            # ── APPROVED (room must be set to occupied) ──
            (0,  rooms_h0[2],  sem1, 'approved', MANAGER_NOTES_APPROVE[0]),   # Aisha → A03 (was available)
            (1,  rooms_h0[5],  sem1, 'approved', MANAGER_NOTES_APPROVE[1]),   # Brian → A06 (was available, now occupied)
            (2,  rooms_h0[9],  sem1, 'approved', MANAGER_NOTES_APPROVE[2]),   # Christine → B04 shared
            (4,  rooms_h1[1],  sem1, 'approved', MANAGER_NOTES_APPROVE[3]),   # Esther → D02 double
            (5,  rooms_h1[4],  sem1, 'approved', MANAGER_NOTES_APPROVE[4]),   # Frank → D05 double
            (7,  rooms_h2[4],  sem1, 'approved', MANAGER_NOTES_APPROVE[0]),   # Henry → shared 1015 occupied
            (9,  rooms_h3[1],  sem1, 'approved', MANAGER_NOTES_APPROVE[1]),   # John → NC102 double
            (11, rooms_h3[4],  sem1, 'approved', MANAGER_NOTES_APPROVE[2]),   # Lawrence → NC203
            (13, rooms_h3[7],  sem1, 'approved', MANAGER_NOTES_APPROVE[3]),   # Nathan → NC206
            (15, rooms_h1[6],  sem1, 'approved', MANAGER_NOTES_APPROVE[4]),   # Patrick → S03 single

            # ── PENDING ──
            (3,  rooms_h0[0],  sem1, 'pending', ''),   # David → A01
            (6,  rooms_h0[3],  sem1, 'pending', ''),   # Gloria → A04
            (8,  rooms_h1[7],  sem2, 'pending', ''),   # Irene → S04 (maintenance — real edge case)
            (10, rooms_h2[5],  sem1, 'pending', ''),   # Karen → 2011
            (12, rooms_h3[2],  sem2, 'pending', ''),   # Martha → NC103
            (16, rooms_h0[6],  sem2, 'pending', ''),   # Queen → A07
            (18, rooms_h1[2],  sem2, 'pending', ''),   # Sandra → D03

            # ── REJECTED ──
            (14, rooms_h0[1],  sem1, 'rejected', MANAGER_NOTES_REJECT[0]),  # Olivia → A02
            (17, rooms_h2[6],  sem1, 'rejected', MANAGER_NOTES_REJECT[2]),  # Ronald → 2012
            (19, rooms_h3[5],  sem1, 'rejected', MANAGER_NOTES_REJECT[4]),  # Timothy → NC204

            # ── CANCELLED ──
            (0,  rooms_h0[4],  sem2, 'cancelled', ''),   # Aisha cancelled a sem2 attempt
            (5,  rooms_h2[2],  sem2, 'cancelled', ''),   # Frank cancelled
            (9,  rooms_h1[3],  sem2, 'cancelled', ''),   # John cancelled
        ]

        created_bookings = 0
        for sidx, room, sem, status, note in bookings_spec:
            student = students[sidx]
            # Skip if student already has an approved booking for this semester
            # (mirrors the real business rule — only allow one per semester)
            if status == 'approved':
                if Booking.objects.filter(student=student, semester=sem, status='approved').exists():
                    continue

            b = Booking.objects.create(
                student=student, room=room,
                semester=sem, status=status,
                manager_note=note,
            )
            # Keep room status consistent with approved bookings
            if status == 'approved' and room.status != 'occupied':
                room.status = 'occupied'
                room.save()
            created_bookings += 1

        self.stdout.write(self.style.SUCCESS(f'✓  {created_bookings} bookings created (approved/pending/rejected/cancelled)'))

        # ── 8. FEEDBACK MESSAGES ─────────────────────────────────────────────
        # Assign messages to hostels realistically; some read, some unread
        feedback_specs = [
            # (hostel_idx, student_idx, subject_idx, is_read)
            (0, 0,  0,  True),
            (0, 1,  1,  True),
            (0, 3,  6,  False),
            (0, 6,  9,  False),
            (1, 4,  2,  True),
            (1, 5,  3,  True),
            (1, 8,  10, False),
            (1, 2,  4,  False),
            (2, 7,  5,  True),
            (2, 9,  7,  False),
            (2, 10, 11, False),
            (3, 11, 8,  True),
            (3, 13, 0,  False),
            (3, 15, 3,  False),
            (0, 12, 2,  False),
            (1, 14, 6,  True),
            (2, 16, 9,  False),
            (3, 17, 1,  True),
            (0, 18, 4,  False),
            (1, 19, 7,  True),
        ]

        for hidx, sidx, subidx, is_read in feedback_specs:
            hostel = hostels[hidx]
            student = students[sidx]
            subject, message = FEEDBACK_SUBJECTS[subidx]
            FeedbackMessage.objects.create(
                hostel=hostel,
                sender=student,
                sender_name=student.get_full_name(),
                sender_email=student.email,
                subject=subject,
                message=message,
                is_read=is_read,
            )

        total_feedback = FeedbackMessage.objects.count()
        unread = FeedbackMessage.objects.filter(is_read=False).count()
        self.stdout.write(self.style.SUCCESS(f'✓  {total_feedback} feedback messages ({unread} unread)'))

        # ── SUMMARY ───────────────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 56)
        self.stdout.write(self.style.SUCCESS('  DEMO DATA POPULATED SUCCESSFULLY'))
        self.stdout.write('─' * 56)
        self.stdout.write('\n  LOGIN CREDENTIALS (password same for all in role)\n')
        self.stdout.write(f'  {"Role":<12} {"Username":<18} {"Password"}')
        self.stdout.write(f'  {"────":<12} {"────────":<18} {"────────"}')
        self.stdout.write(f'  {"Admin":<12} {"admin":<18} Admin@1234')
        for uname, fname, lname, *_ in managers_data:
            self.stdout.write(f'  {"Manager":<12} {uname:<18} Manager@1234')
        self.stdout.write(f'  {"Students":<12} {"nakato_s … byarugaba_t":<18} Student@1234')
        self.stdout.write('\n  All 20 student usernames follow the pattern:')
        self.stdout.write('  nakato_s, opio_b, namirembe_c, ssali_d, akello_e,')
        self.stdout.write('  mugisha_f, nambi_g, okello_h, aciro_i, wasswa_j,')
        self.stdout.write('  nakabugo_k, lubega_l, namusisi_m, oryem_n, atuhaire_o,')
        self.stdout.write('  kiggundu_p, nansubuga_q, tumwebaze_r, namukasa_s, byarugaba_t')
        self.stdout.write('─' * 56 + '\n')
