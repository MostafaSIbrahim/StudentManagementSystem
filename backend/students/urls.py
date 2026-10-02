from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.student_page, name="student-page",),
    path("api/students/", views.student_list, name="student-list",),
    path("api/students/create/", views.student_create, name="student-create",),
    path("api/students/<int:pk>/update/", views.student_update, name="student-update",),
    path("api/students/<int:pk>/delete/", views.student_delete, name="student-delete",),
    ]