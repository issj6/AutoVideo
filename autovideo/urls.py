"""
URL configuration for autovideo project.

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
# from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import SimpleRouter

import files.views
from tasks.views import TaskView, FunctionView
from users.views import RegisterView, LoginTokenObtainPairView, UserView

from rest_framework_simplejwt.views import TokenObtainPairView

router = SimpleRouter()
router.register("user", UserView)
router.register("task", TaskView, basename='task')
router.register("func", FunctionView, basename='func')

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('api/login/', LoginTokenObtainPairView.as_view()),
    path('api/register/', RegisterView.as_view({"post": "register"})),
    path('api/', include(router.urls)),

    path('api/file/', files.views.FileView.as_view({"post": "upload", "get": "get_files"})),
    path('api/file/<int:fid>/', files.views.FileView.as_view({"delete": "delete_file", "get": "get_down_url"})),
]
