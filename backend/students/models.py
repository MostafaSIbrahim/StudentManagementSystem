from django.db import models

# Create your models here.
class Student(models.Model):
    student_number = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    department = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student_number"]

    def __str__(self):
        return f"{self.student_number} - {self.full_name}"

