from setuptools import find_packages, setup

setup(
    name="rp-sidekick",
    version="1.7.2",
    url="http://github.com/praekeltfoundation/rp-sidekick",
    license="BSD",
    author="Praekelt Foundation",
    author_email="dev@praekeltfoundation.org",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "celery<4.0,>=3.1.15",
        "coreapi>=2.3.3,<3",
        "Django>=2.2.2,<2.3",
        "django-celery>=3.3.0,<3.4",
        "django-environ>=0.4.5,<0.5",
        "django-extensions>=2.1.9,<2.2",
        "django-phonenumber-field>=3.0.1,<3.1",
        "django-prometheus>=1.0.15,<2",
        "djangorestframework>=3.9.1,<4",
        "json2html>=1.2.1,<2",
        "phonenumbers>=8.10.13,<8.11",
        "psycopg2-binary>=2.8.3,<2.9",
        "rapidpro-python>=2.6.1,<2.7",
        "redis>=3.2.1,<3.3",
        "whitenoise>=4.1.2,<4.2",
        "raven>=6.10.0,<7",
        "hashids>=1.2.0,<2",
        "django-filter>=2.1.0,<3",
        "boto3",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
