from django.test import TestCase
from django.urls import reverse

from .models import Role, User

PASSWORD = "Str0ng!pass99"


def make_user(email="teacher@school.test", role=Role.TEACHER, **extra):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Test User",
        role=Role.objects.get(role_name=role),
        **extra,
    )


class RegistrationTests(TestCase):
    def data(self, **overrides):
        data = {
            "full_name": "Ana Reyes",
            "email": "ana@school.test",
            "contact_number": "09171234567",
            "role": Role.objects.get(role_name=Role.TEACHER).pk,
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_register_creates_user_with_hashed_password(self):
        response = self.client.post(reverse("register"), self.data())
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(email="ana@school.test")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_duplicate_email_is_rejected(self):
        make_user(email="ana@school.test")
        response = self.client.post(reverse("register"), self.data())
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.count(), 1)

    def test_mismatched_passwords_are_rejected(self):
        response = self.client.post(reverse("register"), self.data(password2="Different!pass99"))
        self.assertContains(response, "don&#x27;t match")
        self.assertFalse(User.objects.filter(email="ana@school.test").exists())

    def test_invalid_email_is_rejected(self):
        response = self.client.post(reverse("register"), self.data(email="not-an-email"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_cannot_self_register_as_administrator(self):
        admin_role = Role.objects.get(role_name=Role.ADMIN)
        response = self.client.post(reverse("register"), self.data(role=admin_role.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())


class LoginLogoutTests(TestCase):
    def test_valid_login_goes_to_role_dashboard(self):
        make_user()
        response = self.client.post(reverse("login"), {"username": "teacher@school.test", "password": PASSWORD})
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_invalid_login_shows_error(self):
        make_user()
        response = self.client.post(reverse("login"), {"username": "teacher@school.test", "password": "wrong"})
        self.assertContains(response, "Incorrect email or password")

    def test_logout_ends_session(self):
        self.client.force_login(make_user())
        self.client.post(reverse("logout"))
        self.assertRedirects(self.client.get(reverse("dashboard")), f"{reverse('login')}?next={reverse('dashboard')}")


class DashboardAccessTests(TestCase):
    def test_logged_out_user_is_sent_to_login(self):
        for name in ["dashboard", "admin_dashboard", "teacher_dashboard", "profile", "profile_edit"]:
            url = reverse(name)
            self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_each_role_lands_on_its_own_dashboard(self):
        expected = {
            Role.ADMIN: "admin_dashboard",
            Role.TEACHER: "teacher_dashboard",
            Role.NURSE: "nurse_dashboard",
            Role.SECURITY: "security_dashboard",
            Role.PARENT: "parent_dashboard",
        }
        for role, url_name in expected.items():
            self.client.force_login(make_user(email=f"{url_name}@school.test", role=role))
            response = self.client.get(reverse("dashboard"))
            self.assertRedirects(response, reverse(url_name))

    def test_user_cannot_open_another_roles_dashboard(self):
        self.client.force_login(make_user(role=Role.TEACHER))
        response = self.client.get(reverse("admin_dashboard"))
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("nurse_dashboard")).status_code, 302)


class ProfileTests(TestCase):
    def test_profile_shows_own_details_only(self):
        make_user(email="other@school.test")
        self.client.force_login(make_user())
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "teacher@school.test")
        self.assertNotContains(response, "other@school.test")

    def test_update_profile(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.post(
            reverse("profile_edit"),
            {"full_name": "New Name", "email": "new@school.test", "contact_number": "09981234567"},
        )
        self.assertRedirects(response, reverse("profile"))
        user.refresh_from_db()
        self.assertEqual((user.full_name, user.email), ("New Name", "new@school.test"))

    def test_cannot_take_another_users_email(self):
        make_user(email="other@school.test")
        user = make_user()
        self.client.force_login(user)
        response = self.client.post(
            reverse("profile_edit"),
            {"full_name": "Test User", "email": "other@school.test", "contact_number": ""},
        )
        self.assertContains(response, "already exists")
        user.refresh_from_db()
        self.assertEqual(user.email, "teacher@school.test")
