"""
URL configuration for ai_companies_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

from django.contrib import admin
from django.urls import path
from companies import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Student login system
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("companies/", views.companies_list, name="companies_list"),
    # Public view (original)
    path("", views.public_view, name="public_view"),
    path("api/companies/", views.get_companies, name="get_companies"),
    path("api/columns/", views.get_column_config, name="get_column_config"),
    path("api/filter-options/", views.get_filter_options, name="get_filter_options"),
    # Error reporting
    path("api/report-error/", views.report_error, name="report_error"),
]
