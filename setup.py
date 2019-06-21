from setuptools import find_packages, setup

setup(
    name="rp-sidekick",
    version="1.6.2",
    url="http://github.com/praekeltfoundation/rp-sidekick",
    license="BSD",
    author="Praekelt Foundation",
    author_email="dev@praekeltfoundation.org",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "celery==3.1.26post2",
        "coreapi==2.3.3",
        "Django>=2.2.2,<2.3",
        "django-celery==3.2.2",
        "django-environ==0.4.5",
        "django-extensions==2.1.0",
        "django-prometheus>=1.0.15,<2",
        "djangorestframework>=3.9.1,<4",
        "json2html==1.2.1",
        "psycopg2==2.7.1",
        "rapidpro-python==2.4",
        "redis==2.10.6",
        "whitenoise==3.3.1",
        "raven==6.9.0",
        "hashids==1.2.0",
        "django-filter==2.1.0",
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
