from django.shortcuts import render, redirect, get_object_or_404
from .models import TeacherProfile,StudentProfile,CustomUser,ParentProfile
from .forms import TeacherProfileForm, TeacherUserForm,StudentUserForm,StudentProfileForm,parentProfileForm,parentUserForm
from django.contrib.auth import get_user_model,update_session_auth_hash,authenticate,login,logout
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from academics.models import Semester, Subject, SubjectOffering,Course
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from accounts.constants import YEAR_LEVEL_CHOICES, SECTION_CHOICES



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
    try:
        if request.method == "POST":
            user_form = TeacherUserForm(request.POST)
            profile_form = TeacherProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():

            teacher_first_name = profile_form.cleaned_data['first_name']
            teacher_last_name = profile_form.cleaned_data['last_name']
            teacher_email,teacher_username = generate_unique_email(
                teacher_first_name,teacher_last_name,domain="parent.isufst.com"
            )

            user = user_form.save(commit=False)
            user.email = teacher_email
            user.username = teacher_username
            user.set_password(get_random_string(8))
            user.first_login = True
            user.role = 'teacher'
            user.save()

            teacher = profile_form.save(commit=False)
            teacher.user = user
            teacher.save()

            messages.success(request, f"Teacher created! Email: {user.email}")
            return redirect('accounts:manage_teacher')

    except IntegrityError:
        user_form.add_error(None,"Email Already exists.")
    except Exception as error:
        profile_form.add_error(None,f'An Unexpected Error occured: {error}')

    
    else:
        user_form = TeacherUserForm()
        profile_form = TeacherProfileForm()
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'active': 'teacher',
        'teachers' : TeacherProfile.objects.all()
    }

    return render(request, 'dashboard/manageteacher.html', context)


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
    students = StudentProfile.objects.select_related('course').all()

    # Attach subjects to each student
    for student in students:
        offerings = SubjectOffering.objects.filter(
            year=student.year,
            subject__course=student.course
        )
        student.subject_list = [o.subject for o in offerings]

    return render(request, 'dashboard/managestudents.html', {
        'students': students
    })



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
            # ✅ ADD PREFIX to avoid field name collision
            parent_user_form = parentUserForm(request.POST, prefix='parent')
            parent_profile_form = parentProfileForm(request.POST, prefix='parent')
            valid_parent_forms = parent_user_form.is_valid() and parent_profile_form.is_valid()
        else:
            parent_user_form = parentUserForm(prefix='parent')
            parent_profile_form = parentProfileForm(prefix='parent')
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

                messages.success(request, f"Student {student_first} {student_last} added successfully!")
                return redirect('accounts:manage_student')

            except IntegrityError as e:
                user_form.add_error(None, "Email or Student ID already exists.")
                if create_new_parent:
                    parent_user_form.add_error(None, "Parent email already exists.")
            except Exception as error:
                student_form.add_error(None, f"An unexpected error occurred: {str(error)}")

    else:
        user_form = StudentUserForm()
        student_form = StudentProfileForm(semester=semester, course=course)
        # ✅ ADD PREFIX for GET request too
        parent_user_form = parentUserForm(prefix='parent')
        parent_profile_form = parentProfileForm(prefix='parent')

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
    student_profile = get_object_or_404(StudentProfile, pk=student_id)
    
    # Get current semester from student profile or default to '1st'
    semester = request.POST.get('semester', student_profile.semester if hasattr(student_profile, 'semester') else '1st')
    
    if request.method == 'POST':
        selected_parent_id = request.POST.get('parent_select', '').strip()
        parent_action = request.POST.get('parent_action', 'keep')
        create_new_parent = parent_action == 'add' and not selected_parent_id
        
        student_form = StudentProfileForm(request.POST, instance=student_profile, semester=semester, course=student_profile.course.id if student_profile.course else None)
        
        if create_new_parent:
            # ✅ ADD PREFIX to avoid field name collision
            parent_user_form = parentUserForm(request.POST, prefix='parent')
            parent_profile_form = parentProfileForm(request.POST, prefix='parent')
            valid_parent_forms = parent_user_form.is_valid() and parent_profile_form.is_valid()
        else:
            parent_user_form = parentUserForm(prefix='parent')
            parent_profile_form = parentProfileForm(prefix='parent')
            valid_parent_forms = True
        
        if student_form.is_valid() and valid_parent_forms:
            try:
                # Save student
                student = student_form.save()
                
                # Handle subjects
                subject_ids = [int(i) for i in request.POST.getlist('subjects') if i]
                if subject_ids:
                    student.subjects.set(subject_ids)
                
                # Handle parent logic
                if parent_action == 'change' and selected_parent_id:
                    # Change to existing parent
                    parent = ParentProfile.objects.get(pk=int(selected_parent_id))
                    student.parents.set([parent])
                    
                elif parent_action == 'add' and create_new_parent:
                    # Create new parent
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
                    
                    # Add new parent to student
                    student.parents.add(parent_profile)
                
                # If parent_action == 'keep', do nothing with parents
                
                messages.success(request, f'{student.full_name} updated successfully.')
                return redirect('accounts:manage_student')
                
            except IntegrityError as e:
                student_form.add_error(None, "Student ID or email already exists.")
                if create_new_parent:
                    parent_user_form.add_error(None, "Parent email already exists.")
            except Exception as error:
                student_form.add_error(None, f"An unexpected error occurred: {str(error)}")
    else:
        student_form = StudentProfileForm(instance=student_profile, semester=semester, course=student_profile.course.id if student_profile.course else None)
        # ✅ ADD PREFIX for GET request too
        parent_user_form = parentUserForm(prefix='parent')
        parent_profile_form = parentProfileForm(prefix='parent')
    
    # Get subjects filtered by student's course, year, and semester
    subjects = Subject.objects.filter(
        course=student_profile.course,
        semester_number=semester
    )
    
    # Filter by year using SubjectOffering
    subject_ids = SubjectOffering.objects.filter(year=student_profile.year).values_list('subject_id', flat=True)
    subjects = subjects.filter(id__in=subject_ids)
    
    enrolled_subject_ids = student_profile.subjects.values_list('id', flat=True)
    
    # Get current parents and available parents
    current_parents = student_profile.parents.all()
    parents = ParentProfile.objects.exclude(id__in=current_parents).order_by('first_name', 'last_name')
    
    forms_list = [student_form, parent_user_form, parent_profile_form]
    
    context = {
        'student_profile': student_profile,
        'student_form': student_form,
        'parent_user_form': parent_user_form,
        'parent_profile_form': parent_profile_form,
        'current_parents': current_parents,
        'parents': parents,
        'subjects': subjects,
        'enrolled_subject_ids': enrolled_subject_ids,
        'semester': semester,
        'forms_list': forms_list,
    }
    return render(request, 'dashboard/edit_student.html', context)




def delete_student(request, student_id):
    student = get_object_or_404(StudentProfile, student_ID=student_id.strip())
    student_name = f"{student.first_name} {student.last_name}"
    student.delete()
    messages.success(request, f"Student {student_name} has been successfully deleted.")
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
        # Only include subjects assigned to this year in SubjectOffering
        subject_ids = SubjectOffering.objects.filter(year=year).values_list('subject_id', flat=True)
        subjects = subjects.filter(id__in=subject_ids)

    data = [{'id': s.id, 'subject_code': s.subject_code, 'name': s.name} for s in subjects]
    return JsonResponse({'subjects': data})

def manage_parents(request):
    parents = ParentProfile.objects.all()
    return render(request,'dashboard/manage_parents.html',{
        'parents': parents,
        'user_form': parentUserForm(),
        'parent_form': parentProfileForm(),
    })

def add_parent(request):
    try:
        if request.method == 'POST':
            user_form = parentUserForm(request.POST)
            parent_form = parentProfileForm(request.POST)

        if user_form.is_valid() and parent_form.is_valid():
            
            parent_first_name = parent_form.cleaned_data['first_name']
            parent_last_name = parent_form.cleaned_data['last_name']
            parent_email,parent_username =  generate_unique_email(
                parent_first_name,parent_last_name,domain="parent.isufst.com"
            )
            user = user_form.save(commit=False)
            user.email = parent_email
            user.username = parent_username
            user.set_password(get_random_string(8))
            user.role = 'parent'
            user.first_login = True
            user.save()

            parent = parent_form.save(commit=False)
            parent.user = user
            parent.save()

            return redirect('accounts:manage_parent')
    except IntegrityError:
        user_form.add_error(None,"Email Already exists.")
    except Exception as error:
        parent_form.add_error(None,f"An unexpected Errror occured: {error}")
    
    else:
        user_form = parentUserForm()
        parent_form = parentProfileForm()
    return render(request,'dashboard/manage_parents.html',{
        'user_form':user_form,
        'parent_form':parent_form,
        'parents': ParentProfile.objects.all()
    })

def edit_parent(request,parent_id):
    parent = get_object_or_404(ParentProfile,id=parent_id)

    if request.method == "POST":
        parent_form = parentProfileForm(request.POST, instance=parent)

        if parent_form.is_valid():
            parent_form.save()
            messages.success(request,"Parent Updated successfully")
            return redirect('accounts:manage_parent')
    else:
        parent_form = parentProfileForm(instance=parent)
    
    return render (request, 'dashboard/manage_parents.html',{
        'parent':parent,
        'parent_form': parent_form
    })

def delete_parent(request, parent_id):
    parent = get_object_or_404(ParentProfile, id=parent_id)
    if request.method == "POST":
        parent.user.delete()
        parent.delete()
        
        messages.success(request, "Parent successfully deleted.")
    return redirect('accounts:manage_parent')  # redirect to parent list


def change_password(request):
    if request.method == 'POST':
        form = SetPasswordForm(user=request.user,data=request.POST)
        if form.is_valid():
            user = form.save()
            user.first_login = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request,  "Password changes successfully!")
            return redirect('dashboard:admin_dashboard')
    else:
        form = SetPasswordForm(user=request.user)

    return render(request, 'dashboard/change_password.html',{
        'form':form
    })

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST.get('password', '')  # allow blank for first login

        user = authenticate(request, username=username, password=password)
        print('Login attempt:', username, 'Password:', password)
        print('User:', user)


        if user:
            login(request, user)

            if user.first_login:
                return redirect('accounts:change_password')

            # Role-based redirect
            if user.role == 'admin':
                return redirect('dashboard:admin_dashboard')
            elif user.role == 'teacher':
                return redirect('dashboard:teacher_dashboard')
            elif user.role == 'student':
                return redirect('dashboard:student_dashboard')
            elif user.role == 'parent':
                return redirect('dashboard:dashboard')
            else:
                return redirect('accounts:login')

        else:
            messages.error(request, "Invalid Credentials.")

    return render(request, 'dashboard/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')



def accounts_dashboard(request):
    # --- Filters ---
    selected_role = request.GET.get('role')
    selected_year = request.GET.get('year')
    selected_section = request.GET.get('section')
    selected_course = request.GET.get('course')

    # --- Students ---
    student_groups = {}
    if selected_role in ['', 'student']:
        students = StudentProfile.objects.all()
        if selected_year:
            students = students.filter(year=selected_year)
        if selected_section:
            students = students.filter(section=selected_section)
        if selected_course:
            students = students.filter(course__id=selected_course)

        for s in students:
            key = f"{s.year} - {s.section}"
            if key not in student_groups:
                student_groups[key] = []
            student_groups[key].append({
                "first_name": s.first_name,
                "last_name": s.last_name,
                "email": s.user.email,
                "password": s.user.plain_password if hasattr(s.user, 'plain_password') else "N/A",
                "course": s.course.name if s.course else "N/A",
            })

    # --- Parents filtered by their children ---
    parent_groups = []
    if selected_role in ['', 'parent']:
        parents = ParentProfile.objects.all()
        if selected_year or selected_section or selected_course:
            # filter parents whose children match criteria
            filtered_parents = []
            for p in parents:
                children = p.students.all()
                if selected_year:
                    children = children.filter(year=selected_year)
                if selected_section:
                    children = children.filter(section=selected_section)
                if selected_course:
                    children = children.filter(course__id=selected_course)
                if children.exists():
                    filtered_parents.append((p, children))
            parents = [p for p, _ in filtered_parents]

        for p in parents:
            children = ", ".join([f"{c.first_name} {c.last_name}" for c in p.students.all()])
            parent_groups.append({
                "first_name": p.first_name,
                "last_name": p.last_name,
                "children": children,
                "email": p.user.email,
                "password": p.user.plain_password if hasattr(p.user, 'plain_password') else "N/A",
            })

    # --- Teachers ---
    # --- Teachers ---
    teacher_records = []
    if selected_role in ['', 'teacher']:
        teachers = TeacherProfile.objects.all()
        
        # Optional: filter by year/course if selected
        if selected_year:
            teachers = teachers.filter(subjects__year=selected_year).distinct()
        if selected_course:
            teachers = teachers.filter(subjects__subject__course__id=selected_course).distinct()
        
        for t in teachers:
            # attach all subject offerings for template
            t.subject_offerings = t.subjects.all()
            teacher_records.append(t)


    # --- Courses for dropdown ---
    courses = Course.objects.all()

    context = {
        "student_groups": student_groups,
        "parent_groups": parent_groups,
        "teacher_records": teacher_records,
        "courses": courses,
        "selected_year": selected_year,
        "selected_section": selected_section,
        "selected_course": selected_course,
        "selected_role": selected_role,
        "year_levels": YEAR_LEVEL_CHOICES,
        "sections": SECTION_CHOICES,
    }

    return render(request, "dashboard/dashboard_accounts.html", context)