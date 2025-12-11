from django import forms
from .models import Vacancy, Category
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
import requests
from django.core.validators import FileExtensionValidator

class VacancyForm(forms.ModelForm):
    new_category = forms.CharField(
        label='Добавить новую категорию',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название категории (необязательно)'
        })
    )

    class Meta:
        model = Vacancy
        fields = ["title", "company", "description", "categories", "active"]
        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название вакансии'}),
            "company": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название компании'}),
            "categories": forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            "description": forms.Textarea(attrs={"rows": 6, "class": "form-control", 'placeholder': 'Полное описание вакансии'}),
            "active": forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'title': 'Название вакансии',
            'company': 'Компания',
            'description': 'Описание',
            'categories': 'Выберите категории',
            'active': 'Вакансия активна'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['company'].required = True
        self.fields['description'].required = True
        self.fields['categories'].required = False

    def clean_new_category(self):
        new_cat = self.cleaned_data.get('new_category', '').strip()
        if new_cat:
            # проверяем, существует ли уже такая категория
            if Category.objects.filter(name__iexact=new_cat).exists():
                raise ValidationError(f'Категория "{new_cat}" уже существует.')
        return new_cat

    def save(self, commit=True):
        new_cat_name = self.cleaned_data.get('new_category', '').strip()
        if commit:
            vacancy = super().save(commit=True)
            if new_cat_name:
                from django.utils.text import slugify
                slug = slugify(new_cat_name)
                new_category, created = Category.objects.get_or_create(
                    name=new_cat_name,
                    defaults={'slug': slug}
                )
                vacancy.categories.add(new_category)
            return vacancy

        vacancy = super().save(commit=False)
        if new_cat_name:
            self._pending_new_category = new_cat_name
        else:
            self._pending_new_category = None
        return vacancy


class ApplicationForm(forms.Form):
    resume = forms.FileField(
        label='Прикрепить резюме (PDF, DOCX)',
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'rtf'])],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    def save_m2m(self):
        super().save_m2m()
        new_cat_name = getattr(self, '_pending_new_category', None)
        if new_cat_name:
            from django.utils.text import slugify
            slug = slugify(new_cat_name)
            new_category, created = Category.objects.get_or_create(
                name=new_cat_name,
                defaults={'slug': slug}
            )
            self.instance.categories.add(new_category)

User = get_user_model()

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email/Логин",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email или логин", "autofocus": "autofocus"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"})
    )

class RegisterForm(UserCreationForm):
    telegram_username = forms.CharField(label='Имя в Telegram', required=False,
                                        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}))
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Имя пользователя'})

        self.fields['email'].label = 'Email'
        self.fields['email'].required = True
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'E-mail'})

        self.fields['first_name'].label = 'Имя'
        self.fields['first_name'].required = True
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Имя'})

        self.fields['last_name'].label = 'Фамилия'
        self.fields['last_name'].required = True
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Фамилия'})

        if 'role' in self.fields:
            self.fields['role'].label = 'Роль'
            self.fields['role'].widget.attrs.update({'class': 'form-select'})

        if 'password1' in self.fields:
            self.fields['password1'].label = 'Пароль'
            self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        if 'password2' in self.fields:
            self.fields['password2'].label = 'Подтвердите пароль'
            self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтвердите пароль'})

    def clean_telegram_username(self):
        username = self.cleaned_data.get('telegram_username')
        if not username:
            return ''
        username = username.strip()
        if username.startswith('@'):
            username = username[1:]

        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            return username

        if not requests:
            raise ValidationError('Библиотека requests не установлена на сервере; нельзя проверить Telegram username.')

        url = f'https://api.telegram.org/bot{token}/getChat'
        try:
            resp = requests.get(url, params={'chat_id': f'@{username}'}, timeout=8)
            data = resp.json()
        except Exception as e:
            raise ValidationError('Не удалось связаться с Telegram API: %s' % str(e))

        if not data.get('ok'):
            raise ValidationError('Не найден пользователь с таким Telegram username.')

        chat = data.get('result', {})
        chat_id = chat.get('id')
        if not chat_id:
            raise ValidationError('Не удалось получить chat_id из ответа Telegram.')

        self._telegram_chat_id = str(chat_id)
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        chat_id = getattr(self, '_telegram_chat_id', None)
        if chat_id:
            user.telegram_chat_id = chat_id
        if commit:
            user.save()
        return user