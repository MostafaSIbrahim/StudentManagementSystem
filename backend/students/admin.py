from django.contrib import admin
from .models import Student
# Register your models here.
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display=(
        "student_number",
        "full_name",
        "email",
        "department",
        "is_active",
    )
    search_fields = ("student_number", "full_name", "email")
    list_filter = ("is_active", "department")
    readonly_fields = ("created_at", "updated_at")