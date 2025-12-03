from django import forms

from .models import Subject, SubjectOffering


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['course', 'subject_code', 'name', 'semester_number', 'year_level']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'subject_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'semester_number': forms.Select(attrs={'class': 'form-control'}),
            'year_level': forms.Select(attrs={'class': 'form-control'}),
        }


class AssignSubjectForm(forms.ModelForm):
    """
    Used mainly to render consistent widgets on the assignment pages.
    """

    class Meta:
        model = SubjectOffering
        fields = ['subject', 'teacher', 'year', 'section', 'school_year']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'school_year': forms.TextInput(attrs={'class': 'form-control'}),
        }