from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "student_number",
            "full_name",
            "email",
            "department",
            "is_active",
        ]