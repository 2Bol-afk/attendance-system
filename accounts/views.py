from django.shortcuts import render, redirect, get_object_or_404
from .models import TeacherProfile,StudentProfile,CustomUser,ParentProfile
from .forms import TeacherProfileForm, TeacherUserForm,StudentUserForm,StudentProfileForm,parentProfileForm,parentUserForm
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from academics.models import Semester, Subject, SubjectOffering
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError

User = get_user_model()


def generate_unique_email(first_name, last_name, domain='CSS.com'):
    # Base parts
    base = f"{slugify(first_name)}.{slugify(last_name)}"

    # ---- UNIQUE EMAIL ----
    email = f"{base}@{domain}"
    counter = 1
    while CustomUser.objects.filter(email=email).exists():
        email = f"{base}{counter}@{domain}"
        counter += 1   # <-- FIXED (you wrote =+1 which is wrong)

    # ---- UNIQUE USERNAME ----
    username = base
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    return email, username

    


# -------------------------------
# Teacher List / Dashboard
# -------------------------------
def manage_teacher(request):
    teachers = TeacherProfile.objects.select_related('user').all()
    # Provide empty forms so the add-teacher modal can render its input fields
    user_form = TeacherUserForm()
    profile_form = TeacherProfileForm()

    return render(request, 'dashboard/manageteacher.html', {
        'teachers': teachers,
        'user_form': user_form,
        'profile_form': profile_form,
        'active': 'teacher',
    })


# -------------------------------
# Add Teacher
# -------------------------------
def add_teacher(request):
    email = None
    password_generated = None

    if request.method == "POST":
        user_form = TeacherUserForm(request.POST)
        profile_form = TeacherProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # Generate random password
            random_password = get_random_string(8)

            user = user_form.save(commit=False)
            user.set_password(random_password)
            user.first_login = True
            user.role = 'teacher'
            user.save()

            teacher = profile_form.save(commit=False)
            teacher.user = user
            teacher.save()

            email = user.email
            password_generated = random_password

            messages.success(request, f"Teacher created! Email: {email}, Password: {password_generated}")
            return redirect('accounts:manage_teacher')
    else:
        user_form = TeacherUserForm()
        profile_form = TeacherProfileForm()

    return render(request, 'dashboard/manageteacher.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'email': email,
        'password': password_generated,
        'active': 'teacher',
    })


# -------------------------------
# Edit Teacher
# -------------------------------
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)

    if request.method == "POST":
        user_form = TeacherUserForm(request.POST, instance=teacher.user)
        profile_form = TeacherProfileForm(request.POST, instance=teacher)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Teacher updated successfully.")
            return redirect('accounts:manage_teacher')
    else:
        user_form = TeacherUserForm(instance=teacher.user)
        profile_form = TeacherProfileForm(instance=teacher)

    return render(request, 'dashboard/manageteacher.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'teacher': teacher,
        'active': 'teacher',
    })


# -------------------------------
# Delete Teacher
# -------------------------------
@require_POST
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.user.delete()  # Delete both user and profile
    teacher.delete()
    messages.success(request, "Teacher deleted successfully.")
    return redirect('accounts:manage_teacher')

def manage_student(request):
    students = StudentProfile.objects.select_related('course').prefetch_related('subjects').all()
    return render(request, 'dashboard/managestudents.html', {'students': students})

def add_student(request):
    semester = request.POST.get('semester', '1st')
    course = request.POST.get('course', None)
    year = request.POST.get('year', None)

    if request.method == 'POST':
        selected_parent_id = request.POST.get('parent_select', '').strip()
        create_new_parent = not selected_parent_id

        user_form = StudentUserForm(request.POST)
        student_form = StudentProfileForm(request.POST, semester=semester, course=course)

        if create_new_parent:
            parent_user_form = parentUserForm(request.POST)
            parent_profile_form = parentProfileForm(request.POST)
            valid_parent_forms = parent_user_form.is_valid() and parent_profile_form.is_valid()
        else:
            parent_user_form = parentUserForm()
            parent_profile_form = parentProfileForm()
            valid_parent_forms = True

        if user_form.is_valid() and student_form.is_valid() and valid_parent_forms:
            try:
                # Parent handling
                if create_new_parent:
                    parent_first = parent_profile_form.cleaned_data['first_name']
                    parent_last = parent_profile_form.cleaned_data['last_name']
                    parent_email, parent_username = generate_unique_email(
                        parent_first, parent_last, domain="parent.isufst.com"
                    )

                    parent_user = parent_user_form.save(commit=False)
                    parent_user.email = parent_email
                    parent_user.username = parent_username
                    parent_user.set_password(get_random_string(8))
                    parent_user.role = 'parent'
                    parent_user.first_login = True
                    parent_user.save()

                    parent_profile = parent_profile_form.save(commit=False)
                    parent_profile.user = parent_user
                    parent_profile.save()
                else:
                    parent_profile = ParentProfile.objects.get(id=int(selected_parent_id))

                # Student handling
                student_first = student_form.cleaned_data['first_name']
                student_last = student_form.cleaned_data['last_name']
                student_email, student_username = generate_unique_email(
                    student_first, student_last, domain="student.isufst.com"
                )

                student_user = user_form.save(commit=False)
                student_user.email = student_email
                student_user.username = student_username
                student_user.set_password(get_random_string(8))
                student_user.role = 'student'
                student_user.first_login = True
                student_user.save()

                student_profile = student_form.save(commit=False)
                student_profile.user = student_user
                student_profile.save()

                # Link student to parent
                student_profile.parents.add(parent_profile)

                # Assign subjects
                subject_ids = [int(i) for i in request.POST.getlist('subjects') if i]
                if subject_ids:
                    student_profile.subjects.set(subject_ids)

                return redirect('accounts:manage_student')

            except IntegrityError:
                user_form.add_error(None, "Email already exists.")
                if create_new_parent:
                    parent_user_form.add_error(None,"Parent email already exists.")
                    parent_profile_form.add_error(None,"Parent already linked.")
                student_form.add_error(None, "Student information duplicate.")
            except Exception as error:
                student_form.add_error(None, f"An unexpected error occurred: {str(error)}")

    else:
        user_form = StudentUserForm()
        student_form = StudentProfileForm(semester=semester, course=course)
        parent_user_form = parentUserForm()
        parent_profile_form = parentProfileForm()

    subjects = Subject.objects.filter(semester_number=semester)
    if course:
        subjects = subjects.filter(course_id=course)
    if year:
        subject_ids = SubjectOffering.objects.filter(year=year).values_list('subject_id', flat=True)
        subjects = subjects.filter(id__in=subject_ids)

    parents = ParentProfile.objects.all().order_by('first_name', 'last_name')

    forms_list = [user_form, student_form, parent_user_form, parent_profile_form]

    return render(request, 'dashboard/add_student.html', {
        'user_form': user_form,
        'student_form': student_form,
        'parent_user_form': parent_user_form,
        'parent_profile_form': parent_profile_form,
        'semester': semester,
        'subjects': subjects,
        'forms_list': forms_list,
        'parents': parents,
    })



def edit_student(request, student_id):
    student_profile = get_object_or_404(StudentProfile, student_ID=student_id)
    student_user = student_profile.user

    # Detect semester
    enrolled_subjects = student_profile.subjects.all()
    detected_semester = enrolled_subjects.first().semester_number if enrolled_subjects.exists() else '1st'
    semester = request.POST.get('semester', detected_semester)
    course = request.POST.get('course', student_profile.course.id if student_profile.course else None)
    year = request.POST.get('year', student_profile.year)

    if request.method == 'POST':
        selected_parent_id = request.POST.get('parent_select', '').strip()
        create_new_parent = request.POST.get('create_new_parent') == 'true'

        # Student forms
        student_form = StudentProfileForm(request.POST, instance=student_profile, semester=semester, course=course)
        user_form = StudentUserForm(request.POST, instance=student_user)

        # Parent forms
        if create_new_parent:
            parent_user_form = parentUserForm(request.POST)
            parent_profile_form = parentProfileForm(request.POST)
            valid_parent_forms = parent_user_form.is_valid() and parent_profile_form.is_valid()
        else:
            parent_user_form = parentUserForm()
            parent_profile_form = parentProfileForm()
            valid_parent_forms = True

        if student_form.is_valid() and user_form.is_valid() and valid_parent_forms:
            try:
                # --- Parent handling ---
                if create_new_parent:
                    # Create parent user
                    parent_first = parent_profile_form.cleaned_data['first_name']
                    parent_last = parent_profile_form.cleaned_data['last_name']
                    parent_email, parent_username = generate_unique_email(parent_first, parent_last)

                    parent_user = parent_user_form.save(commit=False)
                    parent_user.email = parent_email
                    parent_user.username = parent_username
                    parent_user.set_password(get_random_string(8))
                    parent_user.role = 'parent'
                    parent_user.first_login = True
                    parent_user.save()

                    # Create parent profile
                    parent_profile = parent_profile_form.save(commit=False)
                    parent_profile.user = parent_user
                    parent_profile.save()

                    # Link new parent to student
                    student_profile.parents.clear()
                    student_profile.parents.add(parent_profile)

                elif selected_parent_id:
                    # Link to existing parent
                    parent_profile = ParentProfile.objects.get(id=int(selected_parent_id))
                    student_profile.parents.clear()
                    student_profile.parents.add(parent_profile)

                # --- Update student profile ---
                student_profile = student_form.save(commit=False)
                student_profile.user = student_user
                student_profile.save()

                # --- Update subjects ---
                subject_ids = [int(i) for i in request.POST.getlist('subjects') if i]
                student_profile.subjects.set(subject_ids)

                messages.success(request, "Student updated successfully!")
                return redirect('accounts:manage_student')

            except IntegrityError:
                student_form.add_error(None, "A database integrity error occurred (maybe duplicate email/username).")
                if create_new_parent:
                    parent_user_form.add_error(None, "Parent email already exists.")
            except Exception as e:
                student_form.add_error(None, f"Unexpected error: {str(e)}")

    else:
        student_form = StudentProfileForm(instance=student_profile, semester=semester, course=course)
        user_form = StudentUserForm(instance=student_user)
        parent_user_form = parentUserForm()
        parent_profile_form = parentProfileForm()

    # Subjects for current semester/course/year
    subjects = Subject.objects.filter(semester_number=semester)
    if course:
        subjects = subjects.filter(course_id=course)
    if year:
        subject_ids = SubjectOffering.objects.filter(year=year).values_list('subject_id', flat=True)
        subjects = subjects.filter(id__in=subject_ids)

    enrolled_subject_ids = list(student_profile.subjects.values_list('id', flat=True))
    current_parents = student_profile.parents.all()
    parents = ParentProfile.objects.all().order_by('first_name', 'last_name')

    forms_list = [user_form, student_form, parent_user_form, parent_profile_form]

    return render(request, 'dashboard/edit_student.html', {
        'user_form': user_form,
        'student_form': student_form,
        'parent_user_form': parent_user_form,
        'parent_profile_form': parent_profile_form,
        'student_profile': student_profile,
        'semester': semester,
        'subjects': subjects,
        'enrolled_subject_ids': enrolled_subject_ids,
        'current_parents': current_parents,
        'forms_list': forms_list,
        'parents': parents,
    })



def delete_student(request, student_id):
    student_profile = get_object_or_404(StudentProfile, student_ID=student_id)
    
    if request.method == 'POST' or request.method == 'GET':  # Allow GET for now
        student_user = student_profile.user
        student_profile.delete()
        student_user.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('accounts:manage_student')
    
    return redirect('accounts:manage_student')
def load_subjects(request):
    semester = request.GET.get('semester')
    course_id = request.GET.get('course')
    year = request.GET.get('year')

    subjects = Subject.objects.all()

    if semester:
        subjects = subjects.filter(semester_number=semester)
    if course_id:
        subjects = subjects.filter(course_id=course_id)
    if year:
        # Only subjects that have offerings for this year
        subject_ids = SubjectOffering.objects.filter(year=year).values_list('subject_id', flat=True)
        subjects = subjects.filter(id__in=subject_ids)

    data = [{'id': s.id, 'subject_code': s.subject_code, 'name': s.name} for s in subjects]
    return JsonResponse({'subjects': data})


def manage_parents(request):
    parents = ParentProfile.objects.all()
    return render(request,'dashboard/manage_parents.html',{
        'parents': parents
    })

def add_parent(request):
    if request.method == 'POST':
        user_form = parentUserForm(request.POST)
        parent_form = parentProfileForm(request.POST)

        if user_form.is_valid() and parent_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(get_random_string(8))
            user.role = 'parent'
            user.first_login = True
            user.save()

            parent = parent_form.save(commit=False)
            parent.user = user
            parent.save()

            return redirect('accounts:manage_parent')
    else:
        user_form = parentUserForm()
        parent_form = parentProfileForm()
    return render(request,'dashboard/manage_parents.html',{
        'user_form':user_form,
        'parent_form':parent_form
    })






# Login
# -------------------------------
'''def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = None

        if user:
            auth_user = authenticate(request, username=user.username, password=password)
            if auth_user:
                login(request, auth_user)

                if auth_user.first_login:
                    return redirect('accounts:change_password_first_time')
                else:
                    if auth_user.role == 'admin':
                        return redirect('dashboard:dashboard_home')
                    elif auth_user.role == 'teacher':
                        return redirect('dashboard:teacher_home')
                    elif auth_user.role == 'student':
                        return redirect('dashboard:student_home')
            else:
                messages.error(request, "Incorrect password.")
        else:
            messages.error(request, "User with this email does not exist.")

    return render(request, 'accounts/login.html')'''

'''def change_password_first_time(request):
    if request.method == "POST":
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password and new_password == confirm_password:
            request.user.password = make_password(new_password)
            request.user.first_login = False
            request.user.save()
            messages.success(request, "Password changed successfully!")
            return redirect('dashboard:dashboard_home')
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, 'accounts/change_password.html')
'''
