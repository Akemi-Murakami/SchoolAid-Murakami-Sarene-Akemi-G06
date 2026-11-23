from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard"), name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.SchoolAidLoginView.as_view(), name="login"),
    path("logout/", views.SchoolAidLogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("dashboard/nurse/", views.nurse_dashboard, name="nurse_dashboard"),
    path("dashboard/security/", views.security_dashboard, name="security_dashboard"),
    path("dashboard/guardian/", views.parent_dashboard, name="parent_dashboard"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/password/", views.SchoolAidPasswordChangeView.as_view(), name="password_change"),
]
