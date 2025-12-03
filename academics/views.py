# views.py


from .forms import SubjectForm, AssignSubjectForm
from .models import Subject, Course, SubjectOffering, Attendance
from accounts.models import TeacherProfile, StudentProfile
from django.utils import timezone
from datetime import datetime, date
from django.contrib import messages
from django.db.models import Count, Q
import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.constants import YEAR_LEVEL_CHOICES, SECTION_CHOICES

# -------------------------------
# Manage Subjects
# -------------------------------
@login_required
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

@login_required
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject {subject.subject_code} created successfully.')
    return redirect('academics:manage_subjects')

@login_required
def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject {subject.subject_code} updated successfully.')
    return redirect('academics:manage_subjects')

@login_required
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, f'Subject {subject.subject_code} deleted successfully.')
    return redirect('academics:manage_subjects')

# -------------------------------
# Assign Teacher (Page-based)
# -------------------------------
@login_required
def assign_teacher(request):
    # Order by teacher, then year and section for nicer grouping
    offerings = SubjectOffering.objects.select_related('teacher', 'subject').order_by(
        'teacher__last_name',
        'teacher__first_name',
        'year',
        'section',
        'school_year',
    )
    return render(request, 'dashboard/manage_assignteacher.html', {
        'offerings': offerings,
        'active': 'assign_subject',
    })

@login_required
def add_assignment_page(request):
    """
    Page-based assignment:
    - Select teacher (via datalist)
    - Select year level and section
    - Filter subjects by Subject.year_level
    - Prevent duplicate offerings for the same (year, section, subject, school_year)
    - Automatically enroll students by course + year + section
    """
    teacher_list = TeacherProfile.objects.all()

    # Year filter for subjects
    selected_year = request.GET.get('year') or YEAR_LEVEL_CHOICES[0][0]

    subjects = Subject.objects.filter(
        year_level=selected_year
    ).select_related('course').order_by('course__name', 'subject_code')

    # Existing offerings for the chosen year to mark taken sections
    existing_offerings = SubjectOffering.objects.select_related('teacher').filter(
        year=selected_year,
    )
    offerings_by_subject = {
        (offering.subject_id, offering.section): offering
        for offering in existing_offerings
    }

    subject_rows = []
    for subject in subjects:
        section_status = []
        for value, label in SECTION_CHOICES:
            offering = offerings_by_subject.get((subject.id, value))
            section_status.append({
                'value': value,
                'label': label,
                'is_taken': offering is not None,
                'assigned_teacher': offering.teacher if offering else None,
                'school_year': offering.school_year if offering else '',
            })
        subject_rows.append({
            'subject': subject,
            'sections': section_status,
        })

    form = AssignSubjectForm()

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        if not teacher_id:
            messages.error(request, "Please select a valid teacher from the list.")
            return redirect('academics:add_assignment_page')
        teacher = get_object_or_404(TeacherProfile, id=teacher_id)

        year = selected_year
        school_year = request.POST.get('school_year')

        if not year or not school_year:
            messages.error(request, "Year level and school year are required.")
            return redirect('academics:add_assignment_page')

        created_subjects = []
        skipped_subjects = []

        for subject in subjects:
            for section_value, _label in SECTION_CHOICES:
                checkbox_name = f"assign_{subject.id}_{section_value}"
                if checkbox_name not in request.POST:
                    continue

                existing_offering = SubjectOffering.objects.filter(
                    subject=subject,
                    year=year,
                    section=section_value,
                    school_year=school_year,
                ).first()

                if existing_offering:
                    assigned_teacher = existing_offering.teacher
                    if assigned_teacher:
                        skipped_subjects.append(
                            f"{subject.subject_code} - Section {section_value.upper()} "
                            f"(already assigned to {assigned_teacher.first_name} {assigned_teacher.last_name})"
                        )
                    else:
                        skipped_subjects.append(
                            f"{subject.subject_code} - Section {section_value.upper()} (already assigned)"
                        )
                    continue

                offering = SubjectOffering.objects.create(
                    teacher=teacher,
                    subject=subject,
                    year=year,
                    section=section_value,
                    school_year=school_year,
                )

                if offering:
                    created_subjects.append(f"{subject.subject_code} - Section {section_value.upper()}")
                    # Enroll relevant students (course + year + section)
                    students = StudentProfile.objects.filter(
                        course=subject.course,
                        year=year,
                        section=section_value,
                    )
                    for student in students:
                        student.subjects.add(subject)
                else:
                    skipped_subjects.append(f"{subject.subject_code} - Section {section_value.upper()}")

        if created_subjects:
            messages.success(
                request,
                f"Teacher {teacher.first_name} {teacher.last_name} assigned to: "
                f"{', '.join(created_subjects)} (Year {year}, SY {school_year})."
            )
        if skipped_subjects:
            messages.warning(
                request,
                "The following subjects were already assigned for this teacher, year, section, "
                f"and school year and were skipped: {', '.join(skipped_subjects)}."
            )

        return redirect('academics:assign_teacher')

    return render(request, 'dashboard/add_assignment_page.html', {
        'teacher_list': teacher_list,
        'subject_rows': subject_rows,
        'assign_subject_form': form,
        'year_levels': YEAR_LEVEL_CHOICES,
        'sections': SECTION_CHOICES,
        'selected_year': selected_year,
    })

@login_required
def edit_assignment_page(request, offering_id):
    assignment = get_object_or_404(SubjectOffering, id=offering_id)
    teacher_list = TeacherProfile.objects.all()

    # Selected year for filtering subjects (defaults to current assignment year)
    selected_year = request.GET.get('year') or assignment.year

    subjects = Subject.objects.filter(
        year_level=selected_year
    ).select_related('course').order_by('course__name', 'subject_code')

    # Build subject/section grid similar to add page.
    # For the grid we want to show:
    #  - Checked: all combinations currently assigned to this assignment.teacher
    #    for the given year + school_year.
    #  - Disabled: combinations already taken by another teacher (cannot be selected).
    existing_offerings = SubjectOffering.objects.select_related('teacher').filter(
        year=selected_year,
        school_year=assignment.school_year,
    )
    offerings_by_subject_section = {
        (offering.subject_id, offering.section): offering
        for offering in existing_offerings
    }

    subject_rows = []
    for subject in subjects:
        section_status = []
        for value, label in SECTION_CHOICES:
            offering = offerings_by_subject_section.get((subject.id, value))
            # Selected if this combination currently belongs to the assignment's teacher
            is_selected = (
                offering is not None
                and offering.teacher_id == assignment.teacher_id
                and offering.school_year == assignment.school_year
            )
            section_status.append({
                'value': value,
                'label': label,
                'is_selected': is_selected,
                # Taken if another teacher already owns this combination
                'is_taken': offering is not None and offering.teacher_id != assignment.teacher_id,
                'assigned_teacher': offering.teacher if offering and offering.teacher else None,
                'school_year': offering.school_year if offering else '',
            })
        subject_rows.append({
            'subject': subject,
            'sections': section_status,
        })

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        if not teacher_id:
            messages.error(request, "Please select a valid teacher from the list.")
            return redirect('academics:edit_assignment_page', offering_id=offering_id)
        teacher = get_object_or_404(TeacherProfile, id=teacher_id)
        year = request.POST.get('year')
        school_year = request.POST.get('school_year')

        if not year or not school_year:
            messages.error(request, "Year level and school year are required.")
            return redirect('academics:edit_assignment_page', offering_id=offering_id)

        # Determine all selected subject+section combinations from the grid.
        selected_pairs = set()
        for subject in subjects:
            for section_value, _label in SECTION_CHOICES:
                checkbox_name = f"assign_{subject.id}_{section_value}"
                if checkbox_name in request.POST:
                    selected_pairs.add((subject.id, section_value))

        # Check for conflicts: any selected combo that is already assigned to a DIFFERENT teacher.
        if selected_pairs:
            conflicting_offerings = SubjectOffering.objects.filter(
                subject_id__in=[sid for (sid, _sec) in selected_pairs],
                year=year,
                section__in=[sec for (_sid, sec) in selected_pairs],
                school_year=school_year,
            ).exclude(teacher=teacher)

            if conflicting_offerings.exists():
                msg_parts = []
                for conflict in conflicting_offerings:
                    conflict_teacher = conflict.teacher
                    teacher_name = (
                        f"{conflict_teacher.first_name} {conflict_teacher.last_name}"
                        if conflict_teacher else "another teacher"
                    )
                    msg_parts.append(
                        f"{conflict.subject.subject_code} (Year {conflict.year}, "
                        f"Section {conflict.section.upper()}, SY {conflict.school_year}) "
                        f"is already assigned to {teacher_name}"
                    )
                messages.error(request, "Cannot save changes because of conflicts: " + "; ".join(msg_parts))
                return redirect('academics:edit_assignment_page', offering_id=offering_id)

        # Sync offerings for this teacher, year and school year with the selected grid.
        # First, update the base assignment to the chosen teacher/year/SY so it is included in syncing.
        assignment.teacher = teacher
        assignment.year = year
        assignment.school_year = school_year
        assignment.save()

        # Current offerings for this teacher in the given year & school_year.
        current_offerings = SubjectOffering.objects.filter(
            teacher=teacher,
            year=year,
            school_year=school_year,
        )

        current_pairs = {(off.subject_id, off.section): off for off in current_offerings}

        # 1) Remove offerings that are no longer selected.
        for (sub_id, section), off in list(current_pairs.items()):
            if (sub_id, section) not in selected_pairs:
                # Clean up student → subject linkage for this offering before deleting.
                students = StudentProfile.objects.filter(
                    course=off.subject.course,
                    year=off.year,
                    section=off.section,
                )
                for student in students:
                    student.subjects.remove(off.subject)
                off.delete()
                current_pairs.pop((sub_id, section), None)

        # 2) Create new offerings for newly selected combinations.
        created_any = False
        for (sub_id, section_value) in selected_pairs:
            if (sub_id, section_value) in current_pairs:
                # Already exists for this teacher/year/SY -> keep it.
                continue

            subject = get_object_or_404(Subject, id=sub_id)
            new_offering = SubjectOffering.objects.create(
                teacher=teacher,
                subject=subject,
                year=year,
                section=section_value,
                school_year=school_year,
            )
            created_any = True

            # Enroll relevant students (course + year + section)
            students = StudentProfile.objects.filter(
                course=subject.course,
                year=year,
                section=section_value,
            )
            for student in students:
                student.subjects.add(subject)

        # If nothing is selected, we effectively cleared assignments for this teacher/year/SY.
        if not selected_pairs:
            messages.success(
                request,
                f"All subject assignments for {teacher.first_name} {teacher.last_name} "
                f"for Year {year}, SY {school_year} have been cleared."
            )
        else:
            messages.success(
                request,
                f"Assignments updated for {teacher.first_name} {teacher.last_name} "
                f"for Year {year}, SY {school_year}."
            )

        return redirect('academics:assign_teacher')

    return render(request, 'dashboard/edit_assignment_page.html', {
        'assignment': assignment,
        'teacher_list': teacher_list,
        'subjects': subjects,
        'subject_rows': subject_rows,
        'year_levels': YEAR_LEVEL_CHOICES,
        'sections': SECTION_CHOICES,
        'selected_year': selected_year,
    })

@login_required
def delete_assignment(request, offering_id):
    offering = get_object_or_404(SubjectOffering, id=offering_id)
    if request.method == 'POST':
        # Clean up student → subject linkage for this specific offering
        students = StudentProfile.objects.filter(
            course=offering.subject.course,
            year=offering.year,
            section=offering.section,
        )
        for student in students:
            student.subjects.remove(offering.subject)

        offering.delete()
        messages.success(request, "Assignment deleted successfully.")
    return redirect('academics:assign_teacher')

@login_required
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
    # All offerings assigned to this teacher (hard filter)
    offerings = SubjectOffering.objects.filter(teacher=teacher)
    selected_offering = None
    students = StudentProfile.objects.none()  # default empty queryset

    if offering_id:
        # Only allow access to offerings that belong to this teacher
        selected_offering = get_object_or_404(
            SubjectOffering, id=offering_id, teacher=teacher
        )

        # Default filters to the offering's year/section if not explicitly chosen
        if not year:
            year = selected_offering.year
        if not section:
            section = selected_offering.section

        # Filter students by course + year + section
        students = StudentProfile.objects.filter(
            course=selected_offering.subject.course,
            year=year,
            section=section,
        )

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

    # Sections and years for dropdowns – limited strictly to this teacher's offerings
    sections = (
        SubjectOffering.objects.filter(teacher=teacher)
        .values_list('section', flat=True)
        .distinct()
    )
    years = (
        SubjectOffering.objects.filter(teacher=teacher)
        .values_list('year', flat=True)
        .distinct()
    )

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
        messages.success(request, "Attendance has been successfully recorded!")
        return redirect(
            request.path
            + f"?offering={offering_id}&section={section or ''}&year={year or ''}&date={selected_date}&time={selected_time}"
        )

    return render(request, 'dashboard/attendance.html', context)


@login_required
def student_list(request):
    teacher = request.user.teacherprofile

    # Get all offerings for this teacher
    offerings = SubjectOffering.objects.filter(teacher=teacher).select_related(
        'subject'
    )

    # Get filters from GET request
    offering_id = request.GET.get('offering')  # can be empty string
    selected_year = request.GET.get('year')
    selected_section = request.GET.get('section')
    selected_status = request.GET.get('status')

    selected_offering = None
    students = StudentProfile.objects.none()

    if offering_id:  # Only filter by offering if not empty
        # Ensure the offering belongs to the logged-in teacher
        selected_offering = get_object_or_404(
            SubjectOffering, id=offering_id, teacher=teacher
        )
        # Restrict to the exact class (course + year + section) for that offering
        students = StudentProfile.objects.filter(
            course=selected_offering.subject.course,
            year=selected_offering.year,
            section=selected_offering.section,
        )
    else:
        # If no offering selected, show only students that are actually
        # enrolled in subjects taught by this teacher (via SubjectOffering)
        # SubjectOffering has related_name='offerings' on Subject
        students = StudentProfile.objects.filter(
            subjects__offerings__teacher=teacher
        ).distinct()

    # Apply additional filters only if a value is selected
    if selected_year:
        students = students.filter(year=selected_year)
    if selected_section:
        students = students.filter(section=selected_section)
    if selected_status:
        students = students.filter(is_regular=selected_status)

    # Dropdown options – restrict to sections/years from this teacher's offerings
    sections = (
        SubjectOffering.objects.filter(teacher=teacher)
        .values_list('section', flat=True)
        .distinct()
    )
    years = (
        SubjectOffering.objects.filter(teacher=teacher)
        .values_list('year', flat=True)
        .distinct()
    )
    statuses = StudentProfile.objects.values_list('is_regular', flat=True).distinct()

    context = {
        'students': students.distinct(),
        'offerings': offerings,
        'selected_offering': offering_id,
        'sections': sections,
        'years': years,
        'selected_section': selected_section,
        'selected_year': selected_year,
        'statuses': statuses,
        'selected_status': selected_status,
    }

    return render(request, 'dashboard/student_list.html', context)





@login_required
def subject_assign(request):
    teacher = request.user.teacherprofile

    # Get all subject offerings assigned to this teacher
    offerings = SubjectOffering.objects.filter(teacher=teacher).order_by('school_year', 'year')

    context = {
        'offerings': offerings,
    }
    return render(request, 'dashboard/subject_assign.html', context)

