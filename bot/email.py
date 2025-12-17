from django.core.mail import EmailMessage
from django.conf import settings

def send_application_email(application):

    vacancy_title = application.vacancy.title
    student_name = application.student.get_full_name()
    teacher_email = application.vacancy.published_by.email

    subject = f"Отклик на вакансию: {vacancy_title}"
    body = (
        f"Студент {student_name} откликнулся на вакансию.\n\n"
        f"Вакансия: {vacancy_title}\n"
        f"Дата: {application.created_at}\n\n"
        f"Система распределения практики."
    )

    email = EmailMessage(
        subject,
        body,
        settings.EMAIL_HOST_USER,
        [teacher_email]
    )

    if application.resume:
        email.attach_file(application.resume.path)

    email.send()