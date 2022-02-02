from setuptools import find_packages, setup

setup(
    name="rp-sidekick",
    version="1.7.4",
    url="http://github.com/praekeltfoundation/rp-sidekick",
    license="BSD",
    author="Praekelt Foundation",
    author_email="dev@praekeltfoundation.org",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "celery==5.2.3",
        "coreapi==2.3.3",
        "Django==3.2.7",
        "django-environ==0.4.5",
        "django-extensions==3.1.5",
        "django-phonenumber-field==3.0.1",
        "django-prometheus==2.2.0",
        "djangorestframework==3.13.1",
        "json2html==1.3.0",
        "phonenumbers==8.10.23",
        "psycopg2-binary==2.8.6",
        "rapidpro-python==2.6.1",
        "redis==3.2.1",
        "whitenoise==4.1.4",
        "raven==6.10.0",
        "hashids==1.3.1",
        "django-filter==2.4.0",
        "sentry-sdk==1.5.4",
        "dj-database-url==0.5.0",
        "boto3",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
