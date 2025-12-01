from django.urls import path
from . import views
app_name = 'reports'
urlpatterns = [
    path('admin', views.attendance_report, name='attendance_report'),
    path('parent-student',views.parent_student_report,name='parent_student_report'),
    path('student-details/',views.student_details,name='student_details_report'),
    path('teacher-deatil/',views.teacher_details_report,name='teacher_details_report'),
    path('class-overview/',views.class_subject_overview,name='attendance_overview'),
    path('attendance-sumary/',views.attendance_summary,name='attendance_summary'),
    path('detailed-attendance/',views.detailed_attendance,name='detailed_attendance')
]
