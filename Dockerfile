FROM ghcr.io/praekeltfoundation/docker-django-bootstrap-nw:py3.9-bullseye

COPY . /app

RUN pip install -e .

ENV DJANGO_SETTINGS_MODULE "config.settings.production"
RUN SECRET_KEY=placeholder ALLOWED_HOSTS=placeholder python manage.py collectstatic --noinput
CMD [\
    "config.wsgi:application",\
    "--workers=2",\
    "--threads=4",\
    "--worker-class=gthread",\
    "--worker-tmp-dir=/dev/shm"\
]
