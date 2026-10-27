Create users, groups and clients
================================

This guide shows how to create the users, groups and OIDC clients that tests need on the IAM server.
It is meant for developers who test an application against pytest-iam.
These objects are Canaille models:
:class:`~canaille.core.models.User`, :class:`~canaille.core.models.Group` and :class:`~canaille.oidc.basemodels.Client`.
All the tests of a session share the same database: :doc:`how-it-works` explains the consequences.

Create users and groups
-----------------------

Build the objects with the classes of :attr:`iam_server.models <pytest_iam.Server.models>`,
and save them with :attr:`iam_server.backend <pytest_iam.Server.backend>`.
Delete them at the end of the test, so that the following tests do not see them.
In a ``conftest.py`` file, the fixtures are available to all the tests:

.. literalinclude:: examples/conftest.py
    :language: python
    :caption: conftest.py
    :start-at: @pytest.fixture
    :end-at: iam_server.backend.delete(group)

Create random users and groups
------------------------------

When the values do not matter, :meth:`~pytest_iam.Server.random_user` and :meth:`~pytest_iam.Server.random_group`
create and save objects with random values.
Keyword arguments set some of the values.

.. literalinclude:: examples/test_random_users_and_groups.py
    :language: python
    :start-at: @pytest.fixture
    :end-at: iam_server.backend.delete(group)

Register a client
-----------------

The tested application must be registered as an OIDC client before it can log users in.
``redirect_uris`` contains the URL where the application receives the authorization code.

.. literalinclude:: examples/conftest.py
    :language: python
    :caption: conftest.py
    :pyobject: client

.. note::

   The IAM server does not show the consent page to :attr:`trusted <canaille.oidc.basemodels.Client.trusted>` clients.
   A client is trusted when its ``client_uri`` domain matches the ``CANAILLE_OIDC.TRUSTED_DOMAINS`` setting.
   By default, ``.localhost`` and ``127.0.0.1`` are trusted.

Register a client dynamically
-----------------------------

The IAM server implements `OAuth 2.0 dynamic client registration <https://datatracker.ietf.org/doc/html/rfc7591>`_,
without initial access token.
An application that registers itself does not need the ``client`` fixture.
The following test registers a client, and checks it in the database:

.. literalinclude:: examples/test_client_registration.py
    :language: python
    :pyobject: test_dynamic_registration
