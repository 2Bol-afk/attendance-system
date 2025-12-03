from django.db import models
from django.utils import timezone

from accounts.constants import YEAR_LEVEL_CHOICES, SECTION_CHOICES


# Semester
class Semester(models.Model):
    SEMESTER_CHOICES = [('1st', '1st Semester'), ('2nd', '2nd Semester')]
    name = models.CharField(max_length=3, choices=SEMESTER_CHOICES)
    school_year = models.CharField(max_length=10)

    class Meta:
        unique_together = ('name', 'school_year')

    def __str__(self):
        return f"{self.name} - {self.school_year}"


# Course
class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.description}"


# Subject (constant curriculum)
class Subject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    subject_code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    semester_number = models.CharField(
        max_length=3,
        choices=[('1st', '1st Semester'), ('2nd', '2nd Semester')],
    )
    # NEW: Indicates which year level this subject belongs to
    year_level = models.CharField(
        max_length=10,
        choices=YEAR_LEVEL_CHOICES,
        default='1st',
    )

    class Meta:
        unique_together = ('subject_code', 'semester_number', 'year_level')

    def __str__(self):
        course_name = self.course.name if self.course else 'No Course'
        return f"{course_name} - {self.subject_code} - {self.semester_number} - {self.year_level}"


class SubjectOffering(models.Model):
    """
    A concrete offering of a subject for a specific teacher, year level,
    section, and school year.

    The same subject may be offered to multiple sections, but we prevent
    duplicate offerings for the same teacher/subject/year/section/school_year.
    """

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='offerings',
    )
    teacher = models.ForeignKey(
        "accounts.TeacherProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name='subjects',
    )
    year = models.CharField(max_length=10, choices=YEAR_LEVEL_CHOICES)
    section = models.CharField(max_length=5, choices=SECTION_CHOICES, default=SECTION_CHOICES[0][0])
    school_year = models.CharField(max_length=20)

    class Meta:
        unique_together = (
            'subject',
            'year',
            'section',
            'school_year',
        )

    def __str__(self):
        return f"{self.subject.subject_code} - {self.year}{self.section.upper()} - {self.school_year}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    student = models.ForeignKey(
        "accounts.StudentProfile",
        on_delete=models.CASCADE,
        related_name='attendances',
    )
    subject_offering = models.ForeignKey(
        "academics.SubjectOffering",
        on_delete=models.CASCADE,
        related_name='attendances',
    )
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)  # record the time of attendance
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'subject_offering', 'date')

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.subject_offering.subject.subject_code} - "
            f"{self.date} - {self.status}"
        )