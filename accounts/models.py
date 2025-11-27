from django.db import models
from django.contrib.auth.models import AbstractUser
from accounts.constants import YEAR_LEVEL_CHOICES, SECTION_CHOICES, STUDENT_STATUS_CHOICES

# Custom User
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin','Admin'),
        ('teacher','Teacher'),
        ('student','Student'),
        ('parent','Parent')
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    first_login = models.BooleanField(default=True)

# Parent Profile
class ParentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role':'parent'})
    first_name = models.CharField(max_length=50,)
    middle_name = models.CharField(max_length=50,)
    last_name = models.CharField(max_length=50,)
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Teacher Profile
class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role':'teacher'})
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Student Profile (first migration: WITHOUT subjects field)
class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    student_ID = models.CharField(primary_key=True, max_length=10)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    course = models.ForeignKey("academics.Course", on_delete=models.SET_NULL, null=True)
    parents = models.ManyToManyField(ParentProfile, related_name='students', blank=True)
    year = models.CharField(max_length=10, choices=YEAR_LEVEL_CHOICES)
    section = models.CharField(max_length=5, choices=SECTION_CHOICES)
    is_regular = models.CharField(max_length=10, choices=STUDENT_STATUS_CHOICES)

    # subjects field will be added in a second migration
    subjects = models.ManyToManyField("academics.Subject", related_name='students', blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.course.name if self.course else 'No Course'}"
