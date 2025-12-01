from django.urls import path
from . import views
app_name = 'dashboard'
urlpatterns = [
    path('admin/',views.admin_dashboard,name='admin_dashboard'),
    path('teacher/',views.teacher_home,name='teacher_dashboard'),
    path('student/',views.student_dashboard,name='student_dashboard'),
    path('student-subjects/',views.student_subjects,name='student_subjects'),
    path('subject-attendance/',views.student_attendance_overview,name='subject_attendance'),
    path('parent-dashboard', views.parent_dashboard, name='dashboard'),

    # Children list (if parent has multiple students)
    path('children/', views.children_list, name='children_list'),

    # Attendance overview per student
    path('child/<str:student_id>/attendance/', views.student_attendance_overview, name='student_attendance'),

    # Attendance details per subject
    path('child/<str:student_id>/attendance/<str:subject_id>/', views.attendance_detail_per_subject,name='attendance_detail_subject'),
    
]
