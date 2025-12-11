from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime, timedelta
import random
from academics.models import Attendance, SubjectOffering
from accounts.models import StudentProfile


class Command(BaseCommand):
    help = "Populate attendance records for a date range"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            default='2025-11-24',
            help='Start date in YYYY-MM-DD format (default: 2025-11-24)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default='2025-11-28',
            help='End date in YYYY-MM-DD format (default: 2025-11-28)',
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['present', 'absent', 'late', 'random'],
            default='random',
            help='Attendance status to assign (default: random)',
        )

    def handle(self, *args, **options):
        start_date_str = options['start_date']
        end_date_str = options['end_date']
        status_mode = options['status']
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            self.stdout.write(
                self.style.ERROR('Invalid date format. Use YYYY-MM-DD format.')
            )
            return

        if start_date > end_date:
            self.stdout.write(
                self.style.ERROR('Start date must be before or equal to end date.')
            )
            return

        # Get all students
        students = StudentProfile.objects.all()
        if not students.exists():
            self.stdout.write(self.style.WARNING('No students found in the database.'))
            return

        # Get all subject offerings
        offerings = SubjectOffering.objects.all()
        if not offerings.exists():
            self.stdout.write(self.style.WARNING('No subject offerings found in the database.'))
            return

        self.stdout.write(f'Found {students.count()} students and {offerings.count()} subject offerings.')
        self.stdout.write(f'Populating attendance from {start_date} to {end_date}...')

        # Generate date range
        current_date = start_date
        total_created = 0
        total_updated = 0
        status_choices = ['present', 'absent', 'late']

        while current_date <= end_date:
            self.stdout.write(f'\nProcessing date: {current_date}')
            
            for offering in offerings:
                # Get students enrolled in this offering's course, year, and section
                enrolled_students = StudentProfile.objects.filter(
                    course=offering.subject.course,
                    year=offering.year,
                    section=offering.section,
                )
                
                for student in enrolled_students:
                    # Determine status
                    if status_mode == 'random':
                        status = random.choice(status_choices)
                    else:
                        status = status_mode
                    
                    # Generate a random time between 8:00 AM and 5:00 PM
                    hour = random.randint(8, 17)
                    minute = random.randint(0, 59)
                    attendance_time = datetime.combine(current_date, datetime.min.time()).replace(
                        hour=hour, minute=minute
                    ).time()
                    
                    # Create or update attendance record
                    attendance, created = Attendance.objects.update_or_create(
                        student=student,
                        subject_offering=offering,
                        date=current_date,
                        defaults={
                            'status': status,
                            'time': attendance_time,
                        }
                    )
                    
                    if created:
                        total_created += 1
                    else:
                        total_updated += 1

            current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully populated attendance!\n'
                f'Created: {total_created} records\n'
                f'Updated: {total_updated} records\n'
                f'Total: {total_created + total_updated} records'
            )
        )

