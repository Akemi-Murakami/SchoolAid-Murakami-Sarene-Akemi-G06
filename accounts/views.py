from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import Role, User


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. Log in to continue.")
            return redirect("login")
        messages.error(request, "We couldn't create your account. Fix the highlighted fields and try again.")
    return render(request, "accounts/register.html", {"form": form})


class SchoolAidLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().get_short_name()}.")
        return super().form_valid(form)


class SchoolAidLogoutView(LogoutView):
    """Ends the session. Django requires POST for logout."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been logged out.")
        return response


@login_required
def dashboard(request):
    """Send each user to the dashboard for their role."""
    return redirect(request.user.dashboard_url_name)


@role_required(Role.ADMIN)
def admin_dashboard(request):
    roles = Role.objects.annotate(account_count=Count("users")).order_by("role_id")
    recent_users = User.objects.select_related("role").order_by("-created_at")[:5]
    return render(request, "dashboards/admin.html", {"roles": roles, "recent_users": recent_users})


def _role_home(request, title, intro, upcoming):
    context = {"page_title": title, "intro": intro, "upcoming": upcoming}
    return render(request, "dashboards/role_home.html", context)


@role_required(Role.STUDENT)
def student_dashboard(request):
    return _role_home(
        request,
        "Student dashboard",
        "Report an emergency and follow updates on the emergencies you reported.",
        ["Send a one-tap emergency alert", "Choose the emergency type and school location", "Track the status of your reports", "View school safety information"],
    )


@role_required(Role.TEACHER)
def teacher_dashboard(request):
    return _role_home(
        request,
        "Teacher dashboard",
        "Report an incident and follow updates on the emergencies you reported.",
        ["Send a one-tap alert", "Choose the emergency type and school location", "Follow status updates on your reports"],
    )


@role_required(Role.NURSE)
def nurse_dashboard(request):
    return _role_home(
        request,
        "Nurse dashboard",
        "Medical emergency reports will appear here as soon as they are submitted.",
        ["Receive medical report notifications", "Review incident details and affected students", "Update the response status"],
    )


@role_required(Role.SECURITY)
def security_dashboard(request):
    return _role_home(
        request,
        "Security dashboard",
        "Security-related reports will appear here as soon as they are submitted.",
        ["Receive security report notifications", "Monitor active incidents", "Update the response status"],
    )


@role_required(Role.PARENT)
def parent_dashboard(request):
    return _role_home(
        request,
        "Parent and guardian dashboard",
        "Official school announcements about your child will appear here.",
        ["Read verified emergency announcements", "See safety and evacuation instructions", "Find school emergency contacts"],
    )



@login_required
def profile(request):
    return render(request, "accounts/profile.html")


@login_required
def profile_edit(request):

    account = User.objects.get(pk=request.user.pk)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=account)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
        messages.error(request, "Your changes weren't saved. Fix the highlighted fields and try again.")
    return render(request, "accounts/profile_edit.html", {"form": form})


class SchoolAidPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("profile")
    success_message = "Password changed."
