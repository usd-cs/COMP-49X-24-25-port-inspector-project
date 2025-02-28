"""
URL configuration for port_inspector project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from port_inspector_app import views

from . import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("upload/", views.upload_image, name="upload"),
    path("history/", views.view_history, name="history"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),
    path("verify-email/", views.verify_email, name="verify-email"),
    path("verify-email/done/", views.verify_email_done, name="verify-email-done"),
    path(
        "verify-email-confirm/<uidb64>/<token>/",
        views.verify_email_confirm,
        name="verify-email-confirm",
    ),
    path(
        "verify-email/complete/",
        views.verify_email_complete,
        name="verify-email-complete",
    ),
    path("results/", views.results_view, name="results"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# storing uploaded images to our MEDIA_URL
