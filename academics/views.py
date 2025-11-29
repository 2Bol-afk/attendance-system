# views.py

from django.shortcuts import render, redirect, get_object_or_404
from .forms import SubjectForm, AssignSubjectForm
from .models import Subject, Course, SubjectOffering,Attendance
from accounts.models import TeacherProfile,StudentProfile
from django.utils import timezone
from datetime import datetime,date
from django.contrib import messages
from django.db.models import Count, Q
import calendar 

from  accounts.constants import YEAR_LEVEL_CHOICES
# Manage Subjects
def manage_subject(request):
    subjects = Subject.objects.all()
    courses = Course.objects.all()
    add_form = SubjectForm()
    return render(request, 'dashboard/managesubjects.html', {
        'subjects': subjects,
        'add_form': add_form,
        'courses': courses,
        'active': 'subjects',
    })

def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('academics:manage_subjects')

def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
    return redirect('academics:manage_subjects')

def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        subject.delete()
    return redirect('academics:manage_subjects')


# Assign Teacher
def assign_teacher(request):
    teacher_list = TeacherProfile.objects.all()
    offerings = SubjectOffering.objects.all()
    subjects = Subject.objects.all()
    form = AssignSubjectForm()
    return render(request, 'dashboard/manage_assignteacher.html', {
        'teacher': teacher_list,
        'offerings': offerings,
        'subjects': subjects,
        'assign_subject_form': form,
        'active': 'assign_subject',
    })

def add_assignment(request):
    if request.method == 'POST':
        form = AssignSubjectForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('academics:assign_teacher')

def edit_assignment(request, offering_id):
    offering = get_object_or_404(SubjectOffering, id=offering_id)
    if request.method == 'POST':
        form = AssignSubjectForm(request.POST, instance=offering)
        if form.is_valid():
            form.save()
    return redirect('academics:assign_teacher')

def delete_assignment(request, offering_id):
    offering = get_object_or_404(SubjectOffering, id=offering_id)
    if request.method == 'POST':
        offering.delete()
    return redirect('academics:assign_teacher')

def mark_attendance(request):
    teacher = request.user.teacherprofile

    # GET filters
    offering_id = request.GET.get('offering')
    section = request.GET.get('section')
    year = request.GET.get('year')
    selected_date = request.GET.get('date')
    selected_time = request.GET.get('time')
    if not selected_date:
        selected_date = date.today().isoformat()
    if not selected_time:
        selected_time = datetime.now().strftime("%H:%M")
    # All offerings assigned to this teacher
    offerings = SubjectOffering.objects.filter(teacher=teacher)
    selected_offering = None
    students = StudentProfile.objects.none()  # default empty queryset

    if offering_id:
        selected_offering = get_object_or_404(SubjectOffering, id=offering_id)

        # Filter students by course
        students = StudentProfile.objects.filter(course=selected_offering.subject.course)
        if section:
            students = students.filter(section=section)
        if year:
            students = students.filter(year=year)

        # Get existing attendance for pre-selection
        if selected_date and selected_time:
            existing_records = Attendance.objects.filter(
                subject_offering=selected_offering,
                date=selected_date
            )
            existing_attendance = {a.student.student_ID: a.status for a in existing_records}
            for student in students:
                student.attendance_status = existing_attendance.get(student.student_ID, '')
        else:
            for student in students:
                student.attendance_status = ''

    # Sections and years for dropdowns
    sections = StudentProfile.objects.values_list('section', flat=True).distinct()
    years = StudentProfile.objects.values_list('year', flat=True).distinct()

    context = {
        'offerings': offerings,
        'selected_offering': selected_offering,
        'students': students,
        'sections': sections,
        'years': years,
        'selected_section': section,
        'selected_year': year,
        'selected_date': selected_date,
        'selected_time': selected_time,
    }

    # POST: Save attendance
    if request.method == 'POST' and selected_offering and selected_date and selected_time:
        for student in students:
            status = request.POST.get(f'status_{student.student_ID}')
            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    subject_offering=selected_offering,
                    date=selected_date,  # unique_together field
                    defaults={
                        'status': status,
                        'time': selected_time
                    }
                )
        return redirect(request.path + f"?offering={offering_id}&section={section or ''}&year={year or ''}&date={selected_date}&time={selected_time}")

    return render(request, 'dashboard/attendance.html', context)



def student_list(request):
    # Get current logged-in teacher
    teacher = request.user.teacherprofile

    # Get all subject offerings assigned to this teacher
    offerings = SubjectOffering.objects.filter(teacher=teacher)

    # Optional: allow filtering by offering
    offering_id = request.GET.get('offering')
    if offering_id:
        offerings = offerings.filter(id=offering_id)

    # Collect the student queryset
    # Assuming StudentProfile has 'year' and/or 'subjects' relationship
    # Here we fetch all students in the years of the offerings
    years = offerings.values_list('year', flat=True).distinct()
    students = StudentProfile.objects.filter(year__in=years).distinct()

    # For the dropdown filter in template
    context = {
        'students': students,
        'offerings': offerings,
        'selected_offering': offering_id,
    }
    return render(request, 'dashboard/student_list.html', context)



def subject_assign(request):
    teacher = request.user.teacherprofile

    # Get all subject offerings assigned to this teacher
    offerings = SubjectOffering.objects.filter(teacher=teacher).order_by('school_year', 'year')

    context = {
        'offerings': offerings,
    }
    return render(request, 'dashboard/subject_assign.html', context)

