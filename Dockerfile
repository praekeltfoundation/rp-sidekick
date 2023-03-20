FROM ghcr.io/praekeltfoundation/docker-django-bootstrap-nw:py3.9-bullseye

COPY . /app
RUN mkdir -p /app/media/uploads/gpconnect/

RUN pip install -e .

ENV DJANGO_SETTINGS_MODULE "config.settings.production"
RUN SECRET_KEY=placeholder ALLOWED_HOSTS=placeholder python manage.py collectstatic --noinput
CMD ["config.wsgi:application"]
