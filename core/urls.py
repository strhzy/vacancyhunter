from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import UserLoginView, register

urlpatterns = [
    path('', views.vacancy_list, name='vacancy_list'),
    path('vacancy/<int:pk>/', views.vacancy_detail, name='vacancy_detail'),
    path('vacancy/<int:pk>/apply/', views.apply, name='apply'),
    path('my-applications/', views.my_applications, name='my_applications'),

    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/vacancy/new/', views.vacancy_create, name='vacancy_create'),
    path('teacher/vacancy/<int:pk>/edit/', views.vacancy_edit, name='vacancy_edit'),
    path('teacher/vacancy/<int:pk>/apps/', views.vacancy_applications, name='vacancy_applications'),
    path('teacher/vacancy/<int:pk>/delete/', views.vacancy_delete, name='vacancy_delete'),

    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("register/", register, name="register"),
]
    