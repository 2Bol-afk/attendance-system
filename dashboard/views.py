from django.shortcuts import render, redirect

from django.utils import timezone
from accounts.models import TeacherProfile, StudentProfile,ParentProfile
from academics.models import SubjectOffering, Attendance
from django.db.models import Count, Q

# Create your views here.

YEAR_LEVELS = ['1st','2nd','3rd','4th']

def admin_dashboard(request):
    # Get the 5 most recent attendance records with related student and subject_offering
    recent_attendance_list = Attendance.objects.select_related(
        'student',                 # fetch related student
        'subject_offering__subject' # fetch related subject through SubjectOffering
    ).order_by('-date', '-time')[:8]

    # --- Dropdown Filters ---
    selected_year = request.GET.get('year', '1st')
    selected_subject_id = request.GET.get('subject', None)

    subjects_for_year = SubjectOffering.objects.filter(year=selected_year).values_list(
        'subject__id', 'subject__subject_code'
    ).distinct()

    if selected_subject_id is None and subjects_for_year:
        selected_subject_id = subjects_for_year[0][0]

    attendance_qs = Attendance.objects.filter(
        student__year=selected_year,
        subject_offering__subject_id=selected_subject_id
    )

    status_counts = attendance_qs.values('status').annotate(count=Count('id'))
    data = {'present':0, 'absent':0, 'late':0}
    for item in status_counts:
        data[item['status']] = item['count']

    context = {
        'years': YEAR_LEVELS,
        'selected_year': selected_year,
        'subjects': subjects_for_year,
        'selected_subject_id': int(selected_subject_id) if selected_subject_id else None,
        'attendance_data': data,
        'recent_attendance_list': recent_attendance_list,
    }

    return render(request,'dashboard/admindashboard.html', context)

def teacher_home(request):
    teacher = request.user.teacherprofile

    # Subjects assigned to this teacher
    assigned_subjects = SubjectOffering.objects.filter(teacher=teacher)

    # Total subjects assigned
    total_subjects = assigned_subjects.count()

    # Get all students enrolled in the teacher's subjects
    students_set = set()
    for offering in assigned_subjects:
        students_in_offering = offering.subject.students.all()  # assuming Subject has ManyToMany 'students'
        for student in students_in_offering:
            students_set.add(student)

    total_students = len(students_set)

    # Attendance today for these students in teacher's subjects
    today = timezone.now().date()
    total_attendance = Attendance.objects.filter(
        subject_offering__in=assigned_subjects,
        date=today
    ).count()

    context = {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_attendance': total_attendance,
    }
    return render(request, 'dashboard/teacherhome.html', context)


