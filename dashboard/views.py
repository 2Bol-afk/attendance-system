from django.shortcuts import render, redirect,get_object_or_404

from django.utils import timezone
from accounts.models import TeacherProfile, StudentProfile,ParentProfile
from academics.models import SubjectOffering, Attendance,Subject
from django.db.models import Count, Q
from datetime import datetime, date
from django.contrib.auth.decorators import login_required

# Create your views here.

YEAR_LEVELS = ['1st','2nd','3rd','4th']
@login_required
def admin_dashboard(request):

    total_students = StudentProfile.objects.all().count()
    total_teachers = TeacherProfile.objects.all().count()
    total_parents = ParentProfile.objects.all().count()
    total_subjects = Subject.objects.all().count()
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
        'total_students':total_students,
        'total_parents':total_parents,
        'total_subjects':total_subjects,
        'total_teachers':total_teachers
    }

    return render(request,'dashboard/admindashboard.html', context)
@login_required
def teacher_home(request):
    teacher = request.user.teacherprofile

    total_students = StudentProfile.objects.filter(
        subjects__offerings__teacher=teacher
    ).distinct().count()

    total_subjects = SubjectOffering.objects.filter(teacher=teacher).count()
    today = timezone.now().date()
    total_attendance = Attendance.objects.filter(
        subject_offering__teacher=teacher,
        date=today
    ).count()

    # Recent attendance
    recent_attendance_list = Attendance.objects.select_related(
        'student',
        'subject_offering__subject'
    ).filter(subject_offering__teacher=teacher).order_by('-date', '-time')[:5]

    # --- Dropdown Filter for Subjects ---
    selected_subject_id = request.GET.get('subject', None)
    subjects_for_teacher = SubjectOffering.objects.filter(teacher=teacher).values_list(
        'subject__id', 'subject__subject_code'
    ).distinct()

    if selected_subject_id is None and subjects_for_teacher:
        selected_subject_id = subjects_for_teacher[0][0]

    # Attendance overview for selected subject
    attendance_qs = Attendance.objects.filter(
        subject_offering__teacher=teacher,
        subject_offering__subject_id=selected_subject_id
    )

    status_counts = attendance_qs.values('status').annotate(count=Count('id'))
    attendance_data = {'present': 0, 'absent': 0, 'late': 0}
    for item in status_counts:
        attendance_data[item['status']] = item['count']

    context = {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_attendance': total_attendance,
        'recent_attendance_list': recent_attendance_list,
        'subjects_for_teacher': subjects_for_teacher,
        'selected_subject_id': int(selected_subject_id) if selected_subject_id else None,
        'attendance_data': attendance_data,
    }
    return render(request, 'dashboard/teacherhome.html', context)

@login_required
def student_dashboard(request):
    subjects = request.user.studentprofile.subjects.all()
    student = request.user.studentprofile

    assigned_subjects = student.subjects.all()
    total_subjects = assigned_subjects.count()

    attendance_qs = student.attendances.all()

    status_counts = attendance_qs.values('status').annotate(count=Count('id'))

    attendance_data = {'present':0,'absent':0,'late':0}

    for item in status_counts:
        attendance_data[item['status']] = item['count']

    total_records = attendance_qs.count()

    if total_records > 0:
        attendance_percentage = (attendance_data["present"] / total_records) * 100
    else:
        attendance_percentage = 0

    context = {
        'student':student,
        'assigned_subject': assigned_subjects,
        'total_subjects':total_subjects,
        "attendance_data": attendance_data,
        "attendance_percentage": round(attendance_percentage, 1),
        "total_records": total_records,
        'subjects':subjects
    }
    return render(request,'dashboard/student_dashboard.html',context)

@login_required
def student_subjects(request):
    student = request.user.studentprofile
    subjects = student.subjects.all()

    subject_data = []

    for subject in subjects:
        # Get all subject offerings for this subject
        offerings = SubjectOffering.objects.filter(subject=subject)
        
        # Aggregate attendances across all offerings
        attendances = student.attendances.filter(subject_offering__in=offerings)

        total_classes = attendances.count()
        present_count = attendances.filter(status='present').count()
        absent_count = attendances.filter(status='absent').count()
        late_count = attendances.filter(status='late').count()
        attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0

        subject_data.append({
            'name': subject.name,
            'total_classes': total_classes,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'attendance_percentage': round(attendance_percentage, 1),
        })

    context = {
        'subjects': subject_data
    }

    return render(request, 'dashboard/student_subjects.html', context)
@login_required
def student_attendance_overview(request):
    student = request.user.studentprofile
    subjects = student.subjects.all()

    # Get filter values from GET request
    subject_id = request.GET.get('subject')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Default end date is today
    if not end_date:
        end_date = date.today()
    else:
        end_date = date.fromisoformat(end_date)

    # Default start date is first day of current month
    if not start_date:
        start_date = date.today().replace(day=1)
    else:
        start_date = date.fromisoformat(start_date)

    # Ensure start_date and end_date are strings for template inputs
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()

    # Filter attendance records
    attendance_qs = student.attendances.filter(date__range=[start_date, end_date])
    selected_subject = None
    if subject_id:
        attendance_qs = attendance_qs.filter(subject_offering__subject_id=subject_id)
        selected_subject = subjects.get(id=subject_id)

    context = {
        'subjects': subjects,
        'attendance_records': attendance_qs.order_by('-date', '-time'),
        'selected_subject': selected_subject,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'dashboard/student_attendance_overview.html', context)



@login_required
def parent_dashboard(request):

    teacher = request.user.teacherprofile  # Logged-in teacher

    total_students = StudentProfile.objects.filter(
        subjects__offerings__teacher=teacher
    ).distinct().count()

    total_subjects = SubjectOffering.objects.filter(teacher=teacher).count()

    # Total attendance today (for their subjects)
    today = timezone.now().date()
    total_attendance = Attendance.objects.filter(
        subject_offering__teacher=teacher,
        date=today
    ).count()

    # Recent attendance for this teacher only
    recent_attendance_list = Attendance.objects.select_related(
        'student',
        'subject_offering__subject'
    ).filter(subject_offering__teacher=teacher).order_by('-date', '-time')[:5]

    context = {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_attendance': total_attendance,
        'recent_attendance_list': recent_attendance_list,
    }

    return render(request, 'dashboard/teacherhome.html', context)

@login_required
def children_list(request):
    parent = request.user.parentprofile
    children = parent.students.all()

    context = {
        'children': children
    }
    return render(request, 'dashboard/children_list.html', context)

@login_required
def student_attendance_overview(request, student_id):
    student = get_object_or_404(StudentProfile, student_ID=student_id)

    # Subjects dropdown
    subjects = student.subjects.all()
    selected_subject_id = request.GET.get('subject')

    # Always default BOTH to today's date
    today = timezone.now().date()

    start_date = request.GET.get('start_date') or today
    end_date = request.GET.get('end_date') or today

    # Filter logic
    if selected_subject_id:
        selected_subject = subjects.get(id=selected_subject_id)
        offerings = SubjectOffering.objects.filter(subject=selected_subject)
        attendance_records = student.attendances.filter(
            subject_offering__in=offerings,
            date__range=[start_date, end_date]
        )
    else:
        selected_subject = None
        attendance_records = student.attendances.filter(
            date__range=[start_date, end_date]
        )

    context = {
        'student': student,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'start_date': start_date,
        'end_date': end_date,
        'attendance_records': attendance_records.order_by('date', 'time'),
    }
    return render(request, 'dashboard/attendance_overview.html', context)

@login_required
def parent_dashboard(request):
    parent = request.user.parentprofile
    children = parent.students.all()

    selected_child_id = request.GET.get('child')
    selected_subject_id = request.GET.get('subject')
    selected_child = None
    attendance_data = {'present': 0, 'absent': 0, 'late': 0}
    total_subjects = 0
    subjects = []
    recent_attendance_list = []

    if selected_child_id:
        selected_child = children.filter(student_ID=selected_child_id).first()
    elif children.exists():
        selected_child = children.first()

    if selected_child:
        subjects = selected_child.subjects.all()
        total_subjects = subjects.count()

        # Filter attendance by subject if selected
        attendances = selected_child.attendances.all()
        if selected_subject_id:
            attendances = attendances.filter(subject_offering__subject__id=selected_subject_id)

        attendance_data['present'] = attendances.filter(status='present').count()
        attendance_data['absent'] = attendances.filter(status='absent').count()
        attendance_data['late'] = attendances.filter(status='late').count()

        total_classes = attendances.count()
        attendance_percentage = round((attendance_data['present'] / total_classes) * 100, 2) if total_classes > 0 else 0

        # Get recent 10 attendance records
        recent_attendance_list = attendances.order_by('-date')[:10]

    else:
        attendance_percentage = 0

    context = {
        'children': children,
        'selected_child': selected_child,
        'attendance_data': attendance_data,
        'attendance_percentage': attendance_percentage,
        'total_subjects': total_subjects,
        'subjects': subjects,
        'selected_child_id': selected_child_id,
        'selected_subject_id': selected_subject_id,
        'recent_attendance_list': recent_attendance_list,
    }

    return render(request, 'dashboard/parent_dashboard.html', context)




@login_required
def attendance_detail_per_subject(request, student_id, subject_id):
    student = get_object_or_404(StudentProfile, student_ID=student_id)
    subject = get_object_or_404(student.subjects, id=subject_id)

    # Date range filter
    start_date = request.GET.get('start_date') or None
    end_date = request.GET.get('end_date') or timezone.now().date()

    # Get all offerings for this subject
    offerings = SubjectOffering.objects.filter(subject=subject)
    attendances = student.attendances.filter(subject_offering__in=offerings)

    if start_date:
        attendances = attendances.filter(date__range=[start_date, end_date])

    # Summary stats
    total_classes = attendances.count()
    present_count = attendances.filter(status='present').count()
    absent_count = attendances.filter(status='absent').count()
    late_count = attendances.filter(status='late').count()
    attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0

    context = {
        'student': student,
        'subject': subject,
        'attendance_records': attendances.order_by('date', 'time'),
        'total_classes': total_classes,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'attendance_percentage': round(attendance_percentage, 1),
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'parent/attendance_detail_subject.html', context)

@login_required
def parent_student_attendance_overview(request, student_id):
    student = get_object_or_404(StudentProfile, student_ID=student_id)

    # Subjects dropdown
    subjects = student.subjects.all()
    selected_subject_id = request.GET.get('subject')

    # Always default BOTH to today's date
    today = timezone.now().date()

    start_date = request.GET.get('start_date') or today
    end_date = request.GET.get('end_date') or today

    # Filter logic
    if selected_subject_id:
        selected_subject = subjects.get(id=selected_subject_id)
        offerings = SubjectOffering.objects.filter(subject=selected_subject)
        attendance_records = student.attendances.filter(
            subject_offering__in=offerings,
            date__range=[start_date, end_date]
        )
    else:
        selected_subject = None
        attendance_records = student.attendances.filter(
            date__range=[start_date, end_date]
        )

    context = {
        'student': student,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'start_date': start_date,
        'end_date': end_date,
        'attendance_records': attendance_records.order_by('date', 'time'),
    }
    return render(request, 'dashboard/attendance_overview.html', context)


