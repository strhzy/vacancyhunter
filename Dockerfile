FROM python:3.12-slim
WORKDIR /app
EXPOSE 8000

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

ENTRYPOINT ["sh", "-c"]

CMD ["python manage.py migrate --fake-initial --noinput  && gunicorn --bind 0.0.0.0:8000 config.wsgi:application"]