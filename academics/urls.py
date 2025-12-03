# urls.py

from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('subjects/', views.manage_subject, name='manage_subjects'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/edit/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('subjects/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),

    path('assignments/', views.assign_teacher, name='assign_teacher'),
    path('assignments/add-page/', views.add_assignment_page, name='add_assignment_page'),
    path('assignments/edit-page/<int:offering_id>/', views.edit_assignment_page, name='edit_assignment_page'),
    path('assignments/delete/<int:offering_id>/', views.delete_assignment, name='delete_assignment'),



    path('mark-attendance/',views.mark_attendance,name='attendance'),
    path('student-list',views.student_list,name='student_list'),
    path('subject-assign/', views.subject_assign, name='subject_assign'),
]
