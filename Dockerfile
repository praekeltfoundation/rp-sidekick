FROM praekeltfoundation/django-bootstrap:py3.9

COPY . /app
RUN mkdir -p /app/media/uploads/gpconnect/

RUN pip install -e .

# temporary untill there is a new PyCap Release
RUN apt-get-install.sh git
RUN pip install git+git://github.com/redcap-tools/PyCap.git@d9d3dea68640920eefb5d5d095cc62d2968c202d

ENV DJANGO_SETTINGS_MODULE "config.settings.production"
RUN SECRET_KEY=placeholder ALLOWED_HOSTS=placeholder python manage.py collectstatic --noinput
CMD ["config.wsgi:application"]
