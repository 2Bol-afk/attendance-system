# views.py

from django.shortcuts import render, redirect, get_object_or_404
from .forms import SubjectForm, AssignSubjectForm
from .models import Subject, Course, SubjectOffering
from accounts.models import TeacherProfile

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
