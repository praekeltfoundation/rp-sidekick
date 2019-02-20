=================
Rapidpro Sidekick
=================
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
    :alt: Code Style: Black


.. image:: https://codecov.io/gh/praekeltfoundation/rp-sidekick/branch/develop/graph/badge.svg
  :target: https://codecov.io/gh/praekeltfoundation/rp-sidekick
  :alt: Code Coverage


.. image:: https://readthedocs.org/projects/rp-sidekick/badge/?version=latest
    :target: https://rp-sidekick.readthedocs.io/
    :alt: Rapidpro Sidekick Documentation

.. image:: https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg
    :target: https://hub.docker.com/r/praekeltfoundation/rp-sidekick/tags/
    :alt: Docker Automated build

Sidekick is a Django application which provides additional functionality to RapidPro through RapidPro’s webhooks within flow, as well as using RP’s REST API to initiate flows, update contact fields etc.
In some respects it functions much like setting up serverless functions to handle webhooks and return responses. However there are some additional benefits to using a Django application, primarily User authentication and management, as well as management of RapidPro Orgs.

------------------
Local installation
------------------
To set up and run ``rp-sidekick`` locally, do the following::

    $ git clone git@github.com:praekeltfoundation/rp-sidekick.git
    $ cd rp-sidekick
    $ virtualenv ve
    $ source ve/bin/activate
    $ pip install -e .
    $ pip install -r requirements-dev.txt
    $ pre-commit install

RP-Sidekick does not work with SQLite because it uses `JSONFields`_.
This means that you will need to set up PostgreSQL locally. You can spin up a
local db with docker, using the following command::

    $ docker run -d -p 5432:5432 --name=sidekick_db -e POSTGRES_DB=rp_sidekick postgres:9.6

-----
Tools
-----

- `black`_ - this repository uses an opinionated python code formatter. See ``pyproject.toml`` for config.
- `pre-commit`_ - lints staged code as a git pre-commit check. Will prevent commits if linting fails. Currently runs black, flake8 and yamllint.

------------
Contributing
------------

See our `ways of working`_ for a guide on how to contribute to ``rp-sidekick``.

.. _JSONFields: https://docs.djangoproject.com/en/stable/ref/contrib/postgres/fields/#jsonfield
.. _pre-commit: https://pre-commit.com
.. _black: https://github.com/ambv/black
.. _ways of working: ./docs/ways-of-working.md
