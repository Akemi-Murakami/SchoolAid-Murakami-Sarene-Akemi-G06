from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Role, User

MAX_PHOTO_BYTES = 2 * 1024 * 1024


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {
        "invalid_login": "Incorrect email or password, or the account is deactivated. Check your details and try again.",
        "inactive": "This account is deactivated. Contact a school administrator.",
    }

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "contact_number", "role")
        labels = {"role": "I am registering as", "contact_number": "Contact number (optional)"}
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "contact_number": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Administrator accounts are created by the school, never self-registered.
        self.fields["role"].queryset = Role.objects.exclude(role_name=Role.ADMIN).order_by("role_id")
        self.fields["role"].empty_label = "Select your role"
        self.fields["role"].help_text = "Administrator accounts are created by the school."

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("The two passwords don't match.")
        return p2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # hashed
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "email", "contact_number", "profile_photo")
        labels = {"contact_number": "Contact number", "profile_photo": "Profile photo"}
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "contact_number": forms.TextInput(attrs={"inputmode": "tel"}),
            "profile_photo": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if photo and hasattr(photo, "size") and photo.size > MAX_PHOTO_BYTES:
            raise ValidationError("Choose a photo smaller than 2 MB.")
        return photo
