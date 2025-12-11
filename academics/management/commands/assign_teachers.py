from django.core.management.base import BaseCommand
from academics.models import SubjectOffering, Subject
from accounts.models import TeacherProfile
from accounts.constants import YEAR_LEVEL_CHOICES, SECTION_CHOICES
import random


class Command(BaseCommand):
    help = "Assign all teachers to subject offerings"

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-year',
            type=str,
            default='2024-2025',
            help='School year to use for assignments (default: 2024-2025)',
        )
        parser.add_argument(
            '--assign-unassigned-only',
            action='store_true',
            help='Only assign teachers to offerings that currently have no teacher',
        )

    def handle(self, *args, **options):
        school_year = options['school_year']
        assign_unassigned_only = options['assign_unassigned_only']

        # Get all teachers
        teachers = list(TeacherProfile.objects.all())
        if not teachers:
            self.stdout.write(self.style.ERROR('No teachers found in the database.'))
            return

        self.stdout.write(f'Found {len(teachers)} teachers:')
        for teacher in teachers:
            self.stdout.write(f'  - {teacher.first_name} {teacher.last_name}')

        # Get subject offerings
        if assign_unassigned_only:
            offerings = SubjectOffering.objects.filter(teacher__isnull=True)
            self.stdout.write(f'\nFound {offerings.count()} unassigned subject offerings.')
        else:
            offerings = SubjectOffering.objects.all()
            self.stdout.write(f'\nFound {offerings.count()} total subject offerings.')

        if not offerings.exists():
            self.stdout.write(self.style.WARNING('No subject offerings found to assign.'))
            return

        # Strategy: Distribute teachers evenly across offerings
        # If there are more offerings than teachers, some teachers will get multiple assignments
        teacher_index = 0
        assigned_count = 0
        updated_count = 0

        for offering in offerings:
            # Skip if already assigned and we're only assigning unassigned
            if assign_unassigned_only and offering.teacher:
                continue

            # Get a teacher (round-robin distribution)
            teacher = teachers[teacher_index % len(teachers)]
            teacher_index += 1

            # Update the offering
            old_teacher = offering.teacher
            offering.teacher = teacher
            offering.save()

            if old_teacher:
                updated_count += 1
                self.stdout.write(
                    f'Updated: {offering.subject.subject_code} - {offering.year}{offering.section.upper()} '
                    f'(was: {old_teacher.first_name} {old_teacher.last_name}, '
                    f'now: {teacher.first_name} {teacher.last_name})'
                )
            else:
                assigned_count += 1
                self.stdout.write(
                    f'Assigned: {offering.subject.subject_code} - {offering.year}{offering.section.upper()} '
                    f'to {teacher.first_name} {teacher.last_name}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully assigned teachers!\n'
                f'Newly assigned: {assigned_count} offerings\n'
                f'Updated: {updated_count} offerings\n'
                f'Total processed: {assigned_count + updated_count} offerings'
            )
        )

        # Show summary by teacher
        self.stdout.write('\n--- Assignment Summary by Teacher ---')
        for teacher in teachers:
            teacher_offerings = SubjectOffering.objects.filter(teacher=teacher)
            count = teacher_offerings.count()
            if count > 0:
                self.stdout.write(f'\n{teacher.first_name} {teacher.last_name}: {count} subject(s)')
                for offering in teacher_offerings:
                    self.stdout.write(
                        f'  - {offering.subject.subject_code} ({offering.subject.name}) - '
                        f'{offering.year}{offering.section.upper()} - {offering.school_year}'
                    )

