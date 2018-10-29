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

Sidekick Django Web Application for Rapidpro - used to extend the functionality of Rapidpro.

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

-----
Tools
-----

- `black`_ - this repository uses an opinionated python code formatter. See ``pyproject.toml`` for config.
- `pre-commit`_ - lints staged code as a git pre-commit check. Will prevent commits if linting fails. Currently runs black, flake8 and yamllint.

------------
Contributing
------------

See our `ways of working`_ for a guide on how to contribute to ``rp-sidekick``.

.. _pre-commit: https://pre-commit.com
.. _black: https://github.com/ambv/black
.. _ways of working: ./docs/ways-of-working.md
