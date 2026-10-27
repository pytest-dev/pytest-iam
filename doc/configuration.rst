Configuration
#############

This page lists the settings of the pytest-iam server, and the ways to change them.
It is meant for developers who need a server behavior that differs from the default one.
:doc:`how-it-works` explains how these settings are used when the server starts.

Server settings
===============

The :func:`~pytest_iam.iam_configuration` session fixture returns the settings of the server, as a :class:`dict`.
The keys are Flask and Canaille settings, described in :doc:`canaille:references/configuration`.
pytest-iam sets these values:

.. literalinclude:: ../src/pytest_iam/__init__.py
    :language: python
    :pyobject: iam_configuration

The other settings keep their Canaille default value.
The fixture also sets the ``AUTHLIB_INSECURE_TRANSPORT`` environment variable for the whole test process.

To change a setting, redefine the fixture in a ``conftest.py`` file, and edit the dictionary:

.. literalinclude:: examples/configuration_conftest.py
    :language: python
    :caption: conftest.py

Server port
===========

The ``iam_server_port`` session fixture returns the port of the server.
By default, it is a free port, picked when the server starts.
Redefine the fixture to use a fixed port.

Environment variables
=====================

The settings can also be set with environment variables.
A variable name is the setting name, prefixed by ``PYTEST_IAM_``.
Nested settings are separated by ``__``.
For instance, ``PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE`` sets ``iam_configuration["CANAILLE_OIDC"]["REQUIRE_NONCE"]``.

.. code-block:: bash

    env PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE=false pytest

The same variables can be written in a ``.pytest-iam.env`` file, in the current directory.
The ``PYTEST_IAM_`` prefix is also required in this file.

.. code-block:: bash
   :caption: .pytest-iam.env

    PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE=false

Priority
========

A setting can be defined in several sources.
The value from the first source in this list is used:

#. the dictionary returned by :func:`~pytest_iam.iam_configuration`;
#. a ``canaille.toml`` file in the current directory, or the file in the ``CANAILLE_CONFIG`` environment variable;
#. the environment variables prefixed by ``PYTEST_IAM_``;
#. the ``.pytest-iam.env`` file.

The priority applies to each setting.
An environment variable cannot change a value that :func:`~pytest_iam.iam_configuration` sets,
such as ``iam_configuration["CANAILLE"]["ENABLE_REGISTRATION"]``.
To change such a value, redefine the fixture.
