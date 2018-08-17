from setuptools import setup, find_packages

setup(
    name="rp-sidekick",
    version="0.0.1",
    url="http://github.com/praekeltfoundation/rp-sidekick",
    license="BSD",
    author="Praekelt Foundation",
    author_email="dev@praekeltfoundation.org",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "celery==3.1.26post2",
        "Django==2.1",
        "django-celery==3.2.2",
        "django-environ==0.4.5",
        "django-extensions==2.1.0",
        "djangorestframework==3.8.2",
        "psycopg2==2.7.1",
        "PyCap",
        "rapidpro-python==2.4",
        "redis==2.10.6",
        "whitenoise==3.3.1",
        "raven==6.9.0",
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
