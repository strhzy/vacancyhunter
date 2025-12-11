from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from slugify import slugify

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            if not base_slug:
                base_slug = "category"

            slug = base_slug
            counter = 1

            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Vacancy(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    description = models.TextField()
    categories = models.ManyToManyField(Category, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} — {self.company}"

class Application(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    created_at = models.DateTimeField(auto_now_add=True)

    notified_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    class Meta:
        unique_together = ('vacancy', 'student')

    def mark_notified(self):
        self.notified_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.student.get_full_name()} → {self.vacancy}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = [('student','Студент'), ('teacher','Преподаватель')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'
