=================
Rapidpro Sidekick
=================
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

Sidekick app for Rapidpro.

This app is used to extend the functionality of Rapidpro.

------------------
Local installation
------------------

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

.. _pre-commit: https://pre-commit.com
.. _black: https://github.com/ambv/black
