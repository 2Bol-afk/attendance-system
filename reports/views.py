from academics.models import SubjectOffering, Subject, Attendance, Course
from accounts.constants import YEAR_LEVEL_CHOICES,SECTION_CHOICES
from django.shortcuts import render,redirect
from accounts.models import StudentProfile,ParentProfile,TeacherProfile
from django.db.models import Value, F
from django.db.models.functions import Concat,Coalesce
from django.db.models import Count, Q
from django.http import JsonResponse
from collections import defaultdict
from datetime import datetime,date
from django.contrib.auth.decorators import login_required


SEMESTER_CHOICES = [('1st','1st Semester'),('2nd','2nd Semester')]




@login_required
def attendance_report(request):
    courses = Course.objects.all()
    year_levels = YEAR_LEVEL_CHOICES
    semesters = SEMESTER_CHOICES
    sections = SECTION_CHOICES

    course = request.GET.get('course')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    subject = request.GET.get('subject')
    section = request.GET.get('section')

    # Load subjects based on selected course
    subjects = Subject.objects.filter(course__id=course) if course else Subject.objects.all()

    # Base queryset
    report_data = Attendance.objects.select_related(
        'student', 'subject_offering', 'subject_offering__subject'
    )

    # Apply filters
    if course:
        report_data = report_data.filter(student__course__id=course)
    if year:
        report_data = report_data.filter(subject_offering__year=year)
    if semester:
        report_data = report_data.filter(subject_offering__subject__semester_number=semester)
    if subject:
        report_data = report_data.filter(subject_offering__subject__id=subject)
    if section:
        report_data = report_data.filter(student__section=section)

    # Summary
    summary_data = report_data.values(
        'student__student_ID',
        'student__course__name',
    ).annotate(
        full_name=Concat(
            F('student__first_name'),
            Value(' '),
            Coalesce(F('student__middle_name'), Value('')),
            Value(' '),
            F('student__last_name'),
        ),
        total_present=Count('pk', filter=Q(status='present')),
        total_absent=Count('pk', filter=Q(status='absent')),
        total_late=Count('pk', filter=Q(status='late'))
    )

    context = {
        'courses': courses,
        'year_levels': year_levels,
        'semesters': semesters,
        'sections': sections,
        'subjects': subjects,
        'report_data': report_data,
        'summary_data': summary_data,
        'selected_course': course,
        'selected_year': year,
        'selected_semester': semester,
        'selected_subject': subject,
        'selected_section': section,
        'active': 'reports',
    }

    return render(request, 'reports/report.html', context)

@login_required
def parent_student_report(request):
    # Filters
    courses = Course.objects.all()
    year_levels = YEAR_LEVEL_CHOICES
    sections = SECTION_CHOICES

    selected_course = request.GET.get('course')
    selected_year = request.GET.get('year')
    selected_section = request.GET.get('section')

    # Base student queryset
    students = StudentProfile.objects.all()
    if selected_course:
        students = students.filter(course__id=selected_course)
    if selected_year:
        students = students.filter(year=selected_year)
    if selected_section:
        students = students.filter(section=selected_section)

    # Get parents who have these students
    parents = ParentProfile.objects.filter(students__in=students).distinct()

    # Annotate filtered children per parent
    student_ids = students.values_list('student_ID', flat=True)
    for parent in parents:
        parent.filtered_children = parent.students.filter(student_ID__in=student_ids)

    context = {
        'parents': parents,
        'courses': courses,
        'year_levels': year_levels,
        'sections': sections,
        'selected_course': selected_course,
        'selected_year': selected_year,
        'selected_section': selected_section,
        'active': 'reports',
    }
    return render(request, 'reports/parent_children_report.html', context)
@login_required
def student_details(request):
    # Filters
    courses = Course.objects.all()
    year_levels = YEAR_LEVEL_CHOICES
    sections = SECTION_CHOICES

    selected_course = request.GET.get('course')
    selected_year = request.GET.get('year')
    selected_section = request.GET.get('section')

    # Base queryset with prefetch for subjects
    students = StudentProfile.objects.select_related('course').prefetch_related('subjects').all()

    if selected_course:
        students = students.filter(course__id=selected_course)
    if selected_year:
        students = students.filter(year=selected_year)
    if selected_section:
        students = students.filter(section=selected_section)

    context = {
        'students': students,
        'courses': courses,
        'year_levels': year_levels,
        'sections': sections,
        'selected_course': selected_course,
        'selected_year': selected_year,
        'selected_section': selected_section,
        'active': 'reports',
    }
    return render(request, 'reports/student_details.html', context)

@login_required
def teacher_details_report(request):
    courses = Course.objects.all()
    year_levels = StudentProfile._meta.get_field('year').choices
    sections = StudentProfile._meta.get_field('section').choices

    selected_course = request.GET.get('course')
    selected_year = request.GET.get('year')

    teachers_data = []

    teachers = TeacherProfile.objects.all()

    for teacher in teachers:
        # Assigned subjects, filtered by course/year if selected
        subject_offerings = SubjectOffering.objects.filter(teacher=teacher)
        if selected_course:
            subject_offerings = subject_offerings.filter(subject__course_id=selected_course)
        if selected_year:
            subject_offerings = subject_offerings.filter(year=selected_year)

        subjects_info = []

        for so in subject_offerings:
            # Count students in each section
            section_counts = {code: 0 for code, _ in sections}  # initialize
            students_in_subject = StudentProfile.objects.filter(
                subjects=so.subject,
                course=so.subject.course,
                year=so.year
            ).values('section').annotate(count=Count('student_ID'))

            for s in students_in_subject:
                section_counts[s['section']] = s['count']

            subjects_info.append({
                'subject': so.subject,
                'year': so.year,
                'school_year': so.school_year,
                'section_counts': section_counts
            })

        if subjects_info:
            teachers_data.append({
                'teacher': teacher,
                'subjects_info': subjects_info,
                'rowspan': len(subjects_info)
            })

    context = {
        'courses': courses,
        'year_levels': year_levels,
        'sections': sections,
        'selected_course': selected_course,
        'selected_year': selected_year,
        'teachers_data': teachers_data,
    }
    return render(request, 'reports/teacher_details_report.html', context)
@login_required
def class_subject_overview(request):
    teacher = request.user.teacherprofile

    # Filters
    semester = request.GET.get('semester')
    year = request.GET.get('year')
    section = request.GET.get('section')

    offerings = SubjectOffering.objects.filter(teacher=teacher)

    if semester:
        offerings = offerings.filter(subject__semester_number=semester)
    if year:
        offerings = offerings.filter(year=year)

    data = []
    for offering in offerings:
        # Create a list of student counts per section in order of SECTION_CHOICES
        section_counts_list = []
        total_students = 0
        for sec_value, sec_display in SECTION_CHOICES:
            qs = StudentProfile.objects.filter(
                course=offering.subject.course,
                year=offering.year,
                section=sec_value
            )
            # Apply section filter if set
            if section and section != sec_value:
                count = 0
            else:
                count = qs.count()
            section_counts_list.append(count)
            total_students += count

        data.append({
            'subject': offering.subject.name,
            'course': offering.subject.course.name if offering.subject.course else 'N/A',
            'section_counts_list': section_counts_list,
            'total_students': total_students,
            'semester': offering.subject.semester_number,
            'year': offering.year,
            'school_year': offering.school_year,
        })

    context = {
        'data': data,
        'semester_filter': semester,
        'year_filter': year,
        'section_filter': section,
        'semesters': SubjectOffering.objects.values_list('subject__semester_number', flat=True).distinct(),
        'years': SubjectOffering.objects.values_list('year', flat=True).distinct(),
        'sections': SECTION_CHOICES,
        'colspan': 2 + len(SECTION_CHOICES) + 4,
    }
    return render(request, 'reports/class_subject_overview.html', context)
@login_required
def attendance_summary(request):
    teacher = request.user.teacherprofile

    # Filters
    semester = request.GET.get('semester')
    subject_id = request.GET.get('subject')
    section = request.GET.get('section')
    year = request.GET.get('year')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    # Get teacher's subject offerings
    offerings = SubjectOffering.objects.filter(teacher=teacher)

    if semester:
        offerings = offerings.filter(subject__semester_number=semester)
    if subject_id:
        offerings = offerings.filter(subject_id=subject_id)
    if year:
        offerings = offerings.filter(year=year)

    data = []
    for offering in offerings:
        # Filter students by course, year, and section
        students_qs = StudentProfile.objects.filter(course=offering.subject.course, year=offering.year)
        if section:
            students_qs = students_qs.filter(section=section)

        total_in_class = students_qs.count()

        # Attendance counts
        attendance_qs = Attendance.objects.filter(subject_offering=offering)
        if start_date and end_date:
            attendance_qs = attendance_qs.filter(date__range=[start_date, end_date])

        if section:
            attendance_qs = attendance_qs.filter(student__section=section)

        present_count = attendance_qs.filter(status='present').count()
        late_count = attendance_qs.filter(status='late').count()
        absent_count = attendance_qs.filter(status='absent').count()

        avg_attendance = 0
        if total_in_class > 0:
            # calculate average %: (present + late)/total *100
            avg_attendance = round((present_count + late_count) / total_in_class * 100, 2)

        data.append({
            'subject': offering.subject.name,
            'course': offering.subject.course.name if offering.subject.course else 'N/A',
            'section': section if section else 'All',
            'total_in_class': total_in_class,
            'avg_attendance': avg_attendance,
            'present': present_count,
            'late': late_count,
            'absent': absent_count,
            'semester': offering.subject.semester_number,
            'year': offering.year,
            'school_year': offering.school_year,
        })

    context = {
        'start_date':start_date,
        'end_date':end_date,
        'data': data,
        'semester_filter': semester,
        'year_filter': year,
        'section_filter': section,
        'subject_filter': subject_id,
        'semesters': SubjectOffering.objects.values_list('subject__semester_number', flat=True).distinct(),
        'years': SubjectOffering.objects.values_list('year', flat=True).distinct(),
        'sections': SECTION_CHOICES,
        'subjects': SubjectOffering.objects.filter(teacher=teacher).values_list('subject__id','subject__name').distinct(),
    }
    return render(request, 'reports/attendance_summary.html', context)

@login_required
def detailed_attendance(request):
    teacher = request.user.teacherprofile

    # Filters
    subject_id = request.GET.get('subject')
    year = request.GET.get('year')
    section = request.GET.get('section')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_name = request.GET.get('search_name', '').strip()

    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    # Get teacher's subjects
    offerings = SubjectOffering.objects.filter(teacher=teacher)

    if subject_id:
        offerings = offerings.filter(subject_id=subject_id)
    if year:
        offerings = offerings.filter(year=year)

    # Collect attendance records
    attendance_records = Attendance.objects.filter(subject_offering__in=offerings)

    if section:
        attendance_records = attendance_records.filter(student__section=section)
    if start_date and end_date:
        attendance_records = attendance_records.filter(date__range=[start_date, end_date])
    if search_name:
        attendance_records = attendance_records.filter(
            student__first_name__icontains=search_name
        ) | attendance_records.filter(
            student__last_name__icontains=search_name
        )

    attendance_records = attendance_records.select_related('student', 'subject_offering__subject')

    # Prepare data for template
    data = []
    for record in attendance_records:
        data.append({
            'student': f"{record.student.first_name} {record.student.last_name}",
            'subject': record.subject_offering.subject.name,
            'date': record.date,
            'status': record.status.capitalize()
        })

    # Context
    context = {
        'data': data,
        'subject_filter': subject_id,
        'year_filter': year,
        'section_filter': section,
        'start_date': start_date,
        'end_date': end_date,
        'search_name': search_name,
        'sections': SECTION_CHOICES,
        'years': SubjectOffering.objects.filter(teacher=teacher).values_list('year', flat=True).distinct(),
        'subjects': SubjectOffering.objects.filter(teacher=teacher).values_list('subject__id','subject__name').distinct(),
    }

    return render(request, 'reports/detailed_attendance.html', context)
@login_required
def parent_child_summary(request):
    parent = request.user.parentprofile

    # All children of the parent
    children = parent.students.all()


    # 1️⃣ Selected child
    selected_child_id = request.GET.get("child")

    if selected_child_id:
        child = StudentProfile.objects.get(student_ID=selected_child_id)
    else:
        # Default = first child
        child = children.first()

    # 2️⃣ Selected subject
    selected_subject_id = request.GET.get("subject")

    # All subjects the child is enrolled in
    subjects = child.subjects.all()

    # Get all attendance records for the selected child
    attendance_qs = Attendance.objects.filter(student=child)

    # Apply subject filter if selected
    if selected_subject_id:
        attendance_qs = attendance_qs.filter(subject_offering__subject_id=selected_subject_id)

    # ---- Summary Counts ----
    total_present = attendance_qs.filter(status="present").count()
    total_absent = attendance_qs.filter(status="absent").count()
    total_late = attendance_qs.filter(status="late").count()

    total_records = attendance_qs.count()

    # Attendance % calculation
    if total_records > 0:
        attendance_percent = round((total_present / total_records) * 100, 1)
    else:
        attendance_percent = 0

    # ---- Recent Attendance (last 10 records) ----
    recent_attendance = (
        attendance_qs
        .select_related("subject_offering__subject")
        .order_by("-date")[:10]
    )

    recent_rows = [
        {
            "date": att.date.strftime("%b %d, %Y"),
            "subject": att.subject_offering.subject.name,
            "status": att.status
        }
        for att in recent_attendance
    ]

    # ---- Subject Breakdown ----
    breakdown = []

    for subj in subjects:
        subj_records = attendance_qs.filter(subject_offering__subject=subj)

        present = subj_records.filter(status="present").count()
        absent = subj_records.filter(status="absent").count()
        late = subj_records.filter(status="late").count()

        total = subj_records.count()

        percent = round((present / total) * 100, 1) if total > 0 else 0

        breakdown.append({
            "subject": subj.name,
            "present": present,
            "absent": absent,
            "late": late,
            "percent": percent
        })

    context = {
        "children": children,
        "selected_child": child.student_ID,

        "subjects": subjects,
        "selected_subject": selected_subject_id,

        "total_present": total_present,
        "total_absent": total_absent,
        "total_late": total_late,
        "attendance_percent": attendance_percent,

        "recent_attendance": recent_rows,
        "subject_breakdown": breakdown,
    }

    return render(request, "reports/parent_child_summary.html", context)
@login_required
def parent_attendance_timeline(request):
    parent = request.user.parentprofile
    children = StudentProfile.objects.filter(parents=parent)
    
    # Selected child
    selected_child_id = request.GET.get('child')
    if selected_child_id:
        child = children.get(student_ID=selected_child_id)
    else:
        child = children.first()  # default to first child
    
    # Subject filter
    selected_subject = request.GET.get('subject', 'all')
    
    # Status filter
    status_filter = request.GET.get('status', 'all')
    
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base attendance queryset
    attendance_qs = Attendance.objects.filter(student=child)
    
    if selected_subject != 'all':
        attendance_qs = attendance_qs.filter(subject_offering__subject__id=selected_subject)
    
    if status_filter != 'all':
        attendance_qs = attendance_qs.filter(status=status_filter)
    
    if start_date:
        attendance_qs = attendance_qs.filter(date__gte=start_date)
    if end_date:
        attendance_qs = attendance_qs.filter(date__lte=end_date)
    
    # Subjects for the dropdown
    subjects = child.subjects.all()
    
    context = {
        'children': children,
        'selected_child': child,
        'attendance': attendance_qs.order_by('-date'),
        'subjects': subjects,
        'selected_subject': selected_subject,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/attendance_timeline.html', context)