FROM praekeltfoundation/django-bootstrap:py3.6

COPY . /app
RUN pip install -e .

ENV DJANGO_SETTINGS_MODULE "config.settings.production"
RUN SECRET_KEY=placeholder ALLOWED_HOSTS=placeholder python manage.py collectstatic --noinput
CMD ["config.wsgi:application"]
