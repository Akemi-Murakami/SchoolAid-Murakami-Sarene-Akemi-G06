from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models


class Role(models.Model):
    """ROLES table from the SDD: one role can be assigned to many users."""

    ADMIN = "Administrator"
    TEACHER = "Teacher"
    NURSE = "School Nurse"
    SECURITY = "Security Personnel"
    PARENT = "Parent/Guardian"
    ALL = [ADMIN, TEACHER, NURSE, SECURITY, PARENT]

    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.role_name


# Which dashboard (URL name) each role lands on.
ROLE_DASHBOARDS = {
    Role.ADMIN: "admin_dashboard",
    Role.TEACHER: "teacher_dashboard",
    Role.NURSE: "nurse_dashboard",
    Role.SECURITY: "security_dashboard",
    Role.PARENT: "parent_dashboard",
}


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # always hashed, never stored as plain text
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        if "role" not in extra_fields:
            extra_fields["role"], _ = Role.objects.get_or_create(role_name=Role.PARENT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if "role" not in extra_fields:
            extra_fields["role"], _ = Role.objects.get_or_create(role_name=Role.ADMIN)
        return self._create_user(email, password, **extra_fields)


phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-]{7,20}$",
    message="Enter a valid contact number, such as 0917 123 4567.",
)


class User(AbstractBaseUser, PermissionsMixin):
    """USERS table from the SDD. Email is the login name."""

    user_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="users")
    full_name = models.CharField(max_length=150)
    email = models.EmailField(
        max_length=150,
        unique=True,
        error_messages={"unique": "An account with this email already exists."},
    )
    contact_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    is_active = models.BooleanField(default=True)  # account_status: active / inactive
    is_staff = models.BooleanField(default=False)  # can open the Django admin site
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split(" ")[0]

    @property
    def dashboard_url_name(self):
        return ROLE_DASHBOARDS[self.role.role_name]
