from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .models import Student
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from .forms import StudentForm

# Create your views here.
@require_GET
def student_list(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Please Sign In first."},
            status=401,
        )
    if not request.user.has_perm("students.view_student"):
        return JsonResponse(
            {"error" : "You don't have permission to view students"},
            status = 403,
        )
    students = list(
        Student.objects.values(
            "id",
            "student_number",
            "full_name",
            "email",
            "department",
            "is_active",
        )
    )

    return JsonResponse({"students": students})

@login_required
def student_page(request):
    permissions = {
        "can_add": request.user.has_perm("students.add_student"),
        "can_change": request.user.has_perm("students.change_student"),
        "can_delete": request.user.has_perm("students.delete_student"),
    }

    return render(
        request,
        "index.html",
        {"student_permissions": permissions},
    )

@require_POST
def student_create(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Please sign in first."},
            status=401,
        )

    if not request.user.has_perm("students.add_student"):
        return JsonResponse(
            {"error": "You do not have permission to add students."},
            status=403,
        )

    form = StudentForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    try:
        with transaction.atomic():
            student = form.save()
    except IntegrityError:
        return JsonResponse(
            {
                "error":
                    "The record conflicts with existing data. "
                    "Check the student number and try again."
            },
            status=409,
        )

    return JsonResponse(
        {
            "student": {
                "id": student.pk,
                "student_number": student.student_number,
                "full_name": student.full_name,
                "email": student.email,
                "department": student.department,
                "is_active": student.is_active,
            }
        },
        status=201,
    )
@require_POST
def student_update(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Please sign in first."},
            status=401,
        )

    if not request.user.has_perm("students.change_student"):
        return JsonResponse(
            {"error": "You do not have permission to edit students."},
            status=403,
        )

    try:
        with transaction.atomic():
            student = Student.objects.select_for_update().get(pk=pk)
            form = StudentForm(request.POST, instance=student)

            if not form.is_valid():
                return JsonResponse(
                    {"errors": form.errors.get_json_data()},
                    status=400,
                )

            student = form.save()

    except Student.DoesNotExist:
        return JsonResponse(
            {"error": "This student no longer exists."},
            status=404,
        )
    except IntegrityError:
        return JsonResponse(
            {
                "error":
                    "The record conflicts with existing data. "
                    "Check the student number and try again."
            },
            status=409,
        )

    return JsonResponse(
        {
            "student": {
                "id": student.pk,
                "student_number": student.student_number,
                "full_name": student.full_name,
                "email": student.email,
                "department": student.department,
                "is_active": student.is_active,
            }
        }
    )
@require_POST
def student_delete(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Please sign in first."},
            status=401,
        )

    if not request.user.has_perm("students.delete_student"):
        return JsonResponse(
            {"error": "You do not have permission to delete students."},
            status=403,
        )

    try:
        with transaction.atomic():
            student = Student.objects.select_for_update().get(pk=pk)
            student.delete()
    except Student.DoesNotExist:
        return JsonResponse(
            {"error": "This student no longer exists."},
            status=404,
        )

    return JsonResponse({"message": "Student deleted successfully."})