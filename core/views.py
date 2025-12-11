from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .forms import LoginForm, RegisterForm, ApplicationForm
from .models import Vacancy, Category, Application
from .forms import VacancyForm
#from telegram_bot.utils import notify_new_application

#@login_required
def vacancy_list(request):
    categories = Category.objects.all()
    selected_raw = request.GET.get("category", "")
    selected = None
    if selected_raw != "":
        try:
            selected = int(selected_raw)
        except (ValueError, TypeError):
            selected = None

    if selected:
        vacancies = Vacancy.objects.filter(active=True, categories__id=selected).distinct()
    else:
        vacancies = Vacancy.objects.filter(active=True)

    return render(request, "core/student/vacancy_list.html", {
        "vacancies": vacancies,
        "categories": categories,
        "selected": selected,
    })

#@login_required
def vacancy_detail(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    already = False
    if request.user.is_student():
        already = Application.objects.filter(student=request.user, vacancy=vacancy).exists()
    app_form = None
    if request.user.is_authenticated and request.user.is_student() and not already:
        app_form = ApplicationForm()

    return render(request, "core/student/vacancy_detail.html", {
        "vacancy": vacancy,
        "already": already,
        "app_form": app_form,
    })

#@login_required
def apply(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)

    if not request.user.is_student():
        return redirect("vacancy_list")
    if request.method != 'POST':
        return redirect('vacancy_detail', pk=pk)

    form = ApplicationForm(request.POST, request.FILES)
    if not form.is_valid():
        return redirect('vacancy_detail', pk=pk)

    resume = form.cleaned_data.get('resume')

    app, created = Application.objects.get_or_create(student=request.user, vacancy=vacancy)
    if resume:
        app.resume = resume
    if created:
        app.mark_notified()
    app.save()

    return redirect("my_applications")

#@login_required
def my_applications(request):
    apps = Application.objects.filter(student=request.user)
    return render(request, "core/student/my_applications.html", {"apps": apps})

#@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher():
        return redirect("vacancy_list")
    vacancies = Vacancy.objects.filter(published_by=request.user)
    return render(request, "core/teacher/dashboard.html", {"vacancies": vacancies})

#@login_required
def vacancy_create(request):
    if not request.user.is_teacher():
        return redirect("vacancy_list")

    if request.method == "POST":
        form = VacancyForm(request.POST)
        if form.is_valid():
            vac = form.save(commit=False)
            vac.published_by = request.user
            vac.save()
            form.save_m2m()
            return redirect("teacher_dashboard")
    else:
        form = VacancyForm()

    return render(request, "core/teacher/vacancy_form.html", {"form": form})

#@login_required
def vacancy_edit(request, pk):
    vac = get_object_or_404(Vacancy, pk=pk, published_by=request.user)

    if request.method == "POST":
        form = VacancyForm(request.POST, instance=vac)
        if form.is_valid():
            form.save()
            return redirect("teacher_dashboard")
    else:
        form = VacancyForm(instance=vac)

    return render(request, "core/teacher/vacancy_form.html", {"form": form})

def vacancy_delete(request, pk):
    vac = get_object_or_404(Vacancy, pk=pk, published_by=request.user)
    vac.delete()
    return redirect("teacher_dashboard")

#@login_required
def vacancy_applications(request, pk):
    vac = get_object_or_404(Vacancy, pk=pk, published_by=request.user)
    apps = vac.applications.all()
    return render(request, "core/teacher/vacancy_applications.html", {"vac": vac, "apps": apps})

class UserLoginView(LoginView):
    template_name = "core/login.html"
    authentication_form = LoginForm

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("teacher_dashboard")
    else:
        form = RegisterForm()

    return render(request, "core/register.html", {"form": form})