FROM praekeltfoundation/django-bootstrap:py3.6

COPY . /app
RUN pip install -e .

ENV DJANGO_SETTINGS_MODULE "rp_sidekick.settings"
RUN python manage.py collectstatic --noinput
CMD ["rp_sidekick.wsgi:application"]
