from django.core.management.base import BaseCommand
from academics.models import SubjectOffering, Subject
from accounts.models import TeacherProfile, StudentProfile
from accounts.constants import YEAR_LEVEL_CHOICES, SECTION_CHOICES
import random


class Command(BaseCommand):
    help = "Create subject offerings for all subjects and assign teachers to them"

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-year',
            type=str,
            default='2024-2025',
            help='School year to use for assignments (default: 2024-2025)',
        )

    def handle(self, *args, **options):
        school_year = options['school_year']

        # Get all teachers
        teachers = list(TeacherProfile.objects.all())
        if not teachers:
            self.stdout.write(self.style.ERROR('No teachers found in the database.'))
            return

        self.stdout.write(f'Found {len(teachers)} teachers:')
        for teacher in teachers:
            self.stdout.write(f'  - {teacher.first_name} {teacher.last_name}')

        # Get all subjects
        subjects = Subject.objects.select_related('course').all()
        if not subjects.exists():
            self.stdout.write(self.style.ERROR('No subjects found in the database.'))
            return

        self.stdout.write(f'\nFound {subjects.count()} subjects.')

        # Get all students to determine which year/section combinations exist
        students = StudentProfile.objects.all()
        year_section_combinations = set()
        for student in students:
            if student.course and student.year and student.section:
                year_section_combinations.add((student.course, student.year, student.section))

        if not year_section_combinations:
            self.stdout.write(self.style.WARNING('No students found. Creating offerings for all year/section combinations.'))
            # Create for all combinations if no students
            courses = set(s.course for s in subjects if s.course)
            for course in courses:
                for year, _ in YEAR_LEVEL_CHOICES:
                    for section, _ in SECTION_CHOICES:
                        year_section_combinations.add((course, year, section))
        else:
            self.stdout.write(f'Found {len(year_section_combinations)} year/section combinations from students.')

        # Create subject offerings and assign teachers
        teacher_index = 0
        created_count = 0
        skipped_count = 0

        for subject in subjects:
            if not subject.course:
                self.stdout.write(
                    self.style.WARNING(f'Skipping {subject.subject_code} - no course assigned.')
                )
                continue

            # Filter combinations by this subject's course and year_level
            relevant_combinations = [
                (course, year, section)
                for course, year, section in year_section_combinations
                if course == subject.course and year == subject.year_level
            ]

            if not relevant_combinations:
                # If no matching combinations, create for the subject's year_level with all sections
                for section, _ in SECTION_CHOICES:
                    relevant_combinations.append((subject.course, subject.year_level, section))

            for course, year, section in relevant_combinations:
                # Check if offering already exists
                existing = SubjectOffering.objects.filter(
                    subject=subject,
                    year=year,
                    section=section,
                    school_year=school_year,
                ).first()

                if existing:
                    if existing.teacher:
                        skipped_count += 1
                        self.stdout.write(
                            f'Skipped: {subject.subject_code} - {year}{section.upper()} '
                            f'(already assigned to {existing.teacher.first_name} {existing.teacher.last_name})'
                        )
                    else:
                        # Assign teacher to existing offering
                        teacher = teachers[teacher_index % len(teachers)]
                        teacher_index += 1
                        existing.teacher = teacher
                        existing.save()
                        created_count += 1
                        self.stdout.write(
                            f'Assigned teacher to existing: {subject.subject_code} - {year}{section.upper()} '
                            f'to {teacher.first_name} {teacher.last_name}'
                        )
                else:
                    # Create new offering
                    teacher = teachers[teacher_index % len(teachers)]
                    teacher_index += 1
                    offering = SubjectOffering.objects.create(
                        subject=subject,
                        teacher=teacher,
                        year=year,
                        section=section,
                        school_year=school_year,
                    )
                    created_count += 1
                    self.stdout.write(
                        f'Created: {subject.subject_code} ({subject.name}) - {year}{section.upper()} '
                        f'to {teacher.first_name} {teacher.last_name}'
                    )

                    # Enroll relevant students
                    students_to_enroll = StudentProfile.objects.filter(
                        course=course,
                        year=year,
                        section=section,
                    )
                    enrolled_count = 0
                    for student in students_to_enroll:
                        student.subjects.add(subject)
                        enrolled_count += 1
                    if enrolled_count > 0:
                        self.stdout.write(
                            f'  Enrolled {enrolled_count} student(s) in {subject.subject_code}'
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created and assigned!\n'
                f'Created/Assigned: {created_count} offerings\n'
                f'Skipped (already assigned): {skipped_count} offerings'
            )
        )

        # Show summary by teacher
        self.stdout.write('\n--- Assignment Summary by Teacher ---')
        for teacher in teachers:
            teacher_offerings = SubjectOffering.objects.filter(teacher=teacher)
            count = teacher_offerings.count()
            if count > 0:
                self.stdout.write(f'\n{teacher.first_name} {teacher.last_name}: {count} subject(s)')
                for offering in teacher_offerings.order_by('year', 'section', 'subject__subject_code'):
                    self.stdout.write(
                        f'  - {offering.subject.subject_code} ({offering.subject.name}) - '
                        f'{offering.year}{offering.section.upper()} - {offering.school_year}'
                    )

