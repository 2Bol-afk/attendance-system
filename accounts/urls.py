from django.urls import path
from . import views
app_name = 'accounts'
urlpatterns = [
    path("teachers/", views.manage_teacher, name="manage_teacher"),
    path("teachers/add/", views.add_teacher, name="add_teacher"),
    path("teachers/<int:teacher_id>/edit/", views.edit_teacher, name="edit_teacher"),
    path("teachers/<int:teacher_id>/delete/", views.delete_teacher, name="delete_teacher"),
    path('student/',views.manage_student,name='manage_student'),
    path('students/add/',views.add_student,name='add_student'),
    path('student/<str:student_id>/edit/',views.edit_student, name = 'edit_student'),
    path('delete-student/<str:student_id>/',views.delete_student, name='delete_student'),
    path('ajax/load-subjects/', views.load_subjects, name='load_subjects'),
    path('parent/',views.manage_parents,name='manage_parent'),
    path('parent/add/',views.add_parent,name='add_parent'),
    path('parent/<int:parent_id>/edit/',views.edit_parent, name='edit_parent'),
    path('parent/<int:parent_id>/delete/',views.delete_parent,name='delete_parent'),
    path('login/',views.custom_login,name= 'login'),
    path('change-password/',views.change_password,name='change_password'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts-dashboard/',views.accounts_dashboard, name='accounts_dashboard'),
    path('export-accounts/', views.export_accounts_view, name='export_accounts_view'),
]
