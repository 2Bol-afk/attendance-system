# academics/forms.py
from django import forms
from .models import Subject,SubjectOffering

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['course', 'subject_code', 'name', 'semester_number']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'subject_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'semester_number': forms.Select(attrs={'class': 'form-control'}),
        }

class AssignSubjectForm(forms.ModelForm):
    class Meta:
        model =  SubjectOffering
        fields= ['subject','teacher','year','school_year']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.Select(attrs={'class': 'form-control'}),
            # school_year is a free-text field on the model; use TextInput so users can type the school year
            'school_year': forms.TextInput(attrs={'class': 'form-control'}),
            }