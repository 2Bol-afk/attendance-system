from django.db import models
from accounts.constants import YEAR_LEVEL_CHOICES

# Semester
class Semester(models.Model):
    SEMESTER_CHOICES = [('1st','1st Semester'),('2nd','2nd Semester')]
    name = models.CharField(max_length=3, choices=SEMESTER_CHOICES)
    school_year = models.CharField(max_length=10)

    class Meta:
        unique_together = ('name','school_year')

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
    semester_number = models.CharField(max_length=3, choices=[('1st','1st Semester'),('2nd','2nd Semester')])

    class Meta:
        unique_together = ('subject_code','semester_number')

    def __str__(self):
        return f"{self.course.name if self.course else 'No Course'} - {self.subject_code} - {self.semester_number}"

class SubjectOffering(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='offerings')
    teacher = models.ForeignKey("accounts.TeacherProfile", on_delete=models.SET_NULL, null=True) # second migration
    year = models.CharField(max_length=10, choices=YEAR_LEVEL_CHOICES)
    school_year = models.CharField(max_length=20)

    class Meta:
        unique_together = ('subject','school_year','year')

    def __str__(self):
        return f"{self.subject.subject_code} - {self.school_year} - {self.year}"
