from django.contrib import admin
from . models import(
    CustomUser,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
)
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(ParentProfile)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
