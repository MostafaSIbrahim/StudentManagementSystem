from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Permission
from .models import Student


class StudentAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="testadmin",
            email="admin@example.com",
            password="test-password-only",
        )
        cls.viewer = get_user_model().objects.create_user(
            username="no_permissions",
            password="test-password-only",
        )

    def setUp(self):
        self.client.force_login(self.admin)
        self.payload = {
            "student_number": "TEST-001",
            "full_name": "Test Student",
            "email": "student@example.com",
            "department": "Science",
            "is_active": "true",
        }

    def test_create_list_update_delete(self):
        response = self.client.post(
            reverse("students:student-create"),
            self.payload,
        )
        self.assertEqual(response.status_code, 201)
        student_id = response.json()["student"]["id"]
        self.assertTrue(Student.objects.filter(pk=student_id).exists())

        response = self.client.get(reverse("students:student-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["students"][0]["id"], student_id)

        updated = {
            **self.payload,
            "full_name": "Updated Student",
            "is_active": "false",
        }
        response = self.client.post(
            reverse("students:student-update", args=[student_id]),
            updated,
        )
        self.assertEqual(response.status_code, 200)

        student = Student.objects.get(pk=student_id)
        self.assertEqual(student.full_name, "Updated Student")
        self.assertFalse(student.is_active)
        self.assertEqual(Student.objects.count(), 1)

        response = self.client.post(
            reverse("students:student-delete", args=[student_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(pk=student_id).exists())

    def test_duplicate_number_is_rejected(self):
        url = reverse("students:student-create")

        self.assertEqual(
            self.client.post(url, self.payload).status_code,
            201,
        )
        response = self.client.post(url, self.payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("student_number", response.json()["errors"])
        self.assertEqual(Student.objects.count(), 1)

    def test_user_without_permission_cannot_create(self):
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("students:student-create"),
            self.payload,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Student.objects.count(), 0)

    def test_anonymous_user_cannot_list_students(self):
        self.client.logout()

        response = self.client.get(reverse("students:student-list"))

        self.assertEqual(response.status_code, 401)

    def test_invalid_input_is_rejected(self):
        invalid_values = {
            "student_number": "   ",
            "full_name": "   ",
            "email": "not-an-email",
            "department": "   ",
        }

        for field, value in invalid_values.items():
            with self.subTest(field=field):
                payload = {**self.payload, field: value}

                response = self.client.post(
                    reverse("students:student-create"),
                    payload,
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()["errors"])

        self.assertEqual(Student.objects.count(), 0)

    def test_user_without_permission_cannot_update_or_delete(self):
        student = Student.objects.create(
            student_number="TEST-001",
            full_name="Original Name",
            email="student@example.com",
            department="Science",
        )
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("students:student-update", args=[student.pk]),
            {**self.payload, "full_name": "Changed Name"},
        )
        self.assertEqual(response.status_code, 403)

        student.refresh_from_db()
        self.assertEqual(student.full_name, "Original Name")

        response = self.client.post(
            reverse("students:student-delete", args=[student.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())

    def test_update_and_delete_missing_student(self):
        for route in ("student-update", "student-delete"):
            with self.subTest(route=route):
                response = self.client.post(
                    reverse(f"students:{route}", args=[999999]),
                    self.payload,
                )

                self.assertEqual(response.status_code, 404)

    def test_create_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)

        page = csrf_client.get(reverse("students:student-page"))
        self.assertEqual(page.status_code, 200)
        token = csrf_client.cookies["csrftoken"].value

        # A cookie alone is insufficient: the request needs a token too.
        response = csrf_client.post(
            reverse("students:student-create"),
            self.payload,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Student.objects.count(), 0)

        response = csrf_client.post(
            reverse("students:student-create"),
            self.payload,
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Student.objects.count(), 1)

    def test_student_page_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse("students:student-page"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next=/",
        )
        login_page = self.client.get(reverse("login"))
        self.assertTemplateUsed(login_page, "login.html")

    def test_valid_login_opens_student_page(self):
        self.client.logout()

        response = self.client.post(
            reverse("login"),
            {
                "username": "testadmin",
                "password": "test-password-only",
            },
        )

        self.assertRedirects(
            response,
            reverse("students:student-page"),
        )
        self.assertEqual(
            self.client.get(reverse("students:student-list")).status_code,
            200,
        )

    def test_invalid_login_shows_error(self):
        self.client.logout()

        response = self.client.post(
            reverse("login"),
            {
                "username": "testadmin",
                "password": "incorrect-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Sign-in failed. Check your username and password.",
        )
        self.assertEqual(
            self.client.get(reverse("students:student-list")).status_code,
            401,
        )

    def test_logout_ends_session(self):
        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertEqual(
            self.client.get(reverse("students:student-list")).status_code,
            401,
        )
        self.assertRedirects(
            self.client.get(reverse("students:student-page")),
            f"{reverse('login')}?next=/",
        )

    def test_superuser_receives_all_action_permissions(self):
        response = self.client.get(reverse("students:student-page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["student_permissions"],
            {
                "can_add": True,
                "can_change": True,
                "can_delete": True,
            },
        )

    def test_view_only_user_receives_no_action_permissions(self):
        permission = Permission.objects.get(
            content_type__app_label="students",
            content_type__model="student",
            codename="view_student",
        )
        self.viewer.user_permissions.add(permission)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("students:student-page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["student_permissions"],
            {
                "can_add": False,
                "can_change": False,
                "can_delete": False,
            },
        )

        response = self.client.get(reverse("students:student-list"))
        self.assertEqual(response.status_code, 200)

    def test_edit_permission_does_not_enable_add_or_delete(self):
        permissions = Permission.objects.filter(
            content_type__app_label="students",
            content_type__model="student",
            codename__in=["view_student", "change_student"],
        )
        self.viewer.user_permissions.add(*permissions)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("students:student-page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["student_permissions"],
            {
                "can_add": False,
                "can_change": True,
                "can_delete": False,
            },
        )