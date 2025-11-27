from django.contrib import admin
from .models import Subject, Course, Semester, SubjectOffering

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_code', 'name', 'course', 'semester_number')
    search_fields = ('subject_code', 'name', 'course__name')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_year')

@admin.register(SubjectOffering)
class SubjectOfferingAdmin(admin.ModelAdmin):
    list_display = ('subject', 'teacher', 'year','school_year')
    list_filter = ('year','school_year', 'teacher')
    search_fields = ('subject__subject_code', 'teacher__first_name', 'teacher__last_name')

