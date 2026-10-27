How pytest-iam works
====================

This page explains what happens when a test requests the :func:`~pytest_iam.iam_server` fixture,
and which state is shared between tests.
It is meant for developers who already use pytest-iam and want to understand its behavior,
for instance to avoid tests that depend on each other.
It does not explain how to write the tests themselves:
see :doc:`client-applications` and :doc:`resource-servers` for that.

One server for the whole test session
-------------------------------------

:func:`~pytest_iam.iam_server` is a session-scoped fixture.
The first test that needs it starts a `Canaille <https://canaille.readthedocs.io>`_ instance,
and every following test gets the same instance.
The server stops at the end of the test session.

The server is built from the :func:`~pytest_iam.iam_configuration` fixture,
and uses an in-memory database.
It listens on ``localhost``, on a free port picked by the ``iam_server_port`` fixture,
and handles requests in a thread of the test process.
The server handles one request at a time.

During the whole session, the Canaille application context is active.
This lets tests read and write models with :attr:`~pytest_iam.Server.backend` directly.
It also means that :data:`flask.current_app` is the Canaille application in test code,
unless the tested application pushes its own context.

Two ways to reach the server
----------------------------

The server can be reached in two ways, which share the same application and the same data:

- real HTTP requests to :attr:`~pytest_iam.Server.url`, for instance from the OAuth client library of the tested application or from a browser;
- :attr:`~pytest_iam.Server.test_client`, a :class:`werkzeug.test.Client` that calls the application without network.

A user created with :meth:`~pytest_iam.Server.random_user` is visible from both.
The test client needs no network, and returns responses that the test can inspect directly.
Real HTTP is needed when the tested code performs the requests itself,
for instance to fetch the server metadata or to exchange an authorization code.

State shared between tests
--------------------------

Since the server lives for the whole session, its state outlives each test.
The database is not reset between tests.
Users, groups, clients, tokens and consents created by a test stay available to the following tests.
This includes the objects created by :meth:`~pytest_iam.Server.random_user`,
:meth:`~pytest_iam.Server.random_group`, :meth:`~pytest_iam.Server.random_token`
and :meth:`~pytest_iam.Server.consent`.
Fixtures that create objects should delete them after the test,
as the examples of :doc:`client-applications` do with ``iam_server.backend.delete``.

The user session opened by :meth:`~pytest_iam.Server.login` is the exception.
pytest-iam does not store this session in a cookie.
It attaches it to every request, whatever the client.
The ``iam_restore_login`` fixture undoes the :meth:`~pytest_iam.Server.login` calls made during a test
when the test ends.
A session opened by a module or session scoped fixture stays open after the test,
until a call to :meth:`~pytest_iam.Server.logout`.
A user who logs in through the login form gets a regular session cookie instead.
This session only exists in the client that received the cookie.

Configuration sources
---------------------

The server configuration comes from several sources:
the :func:`~pytest_iam.iam_configuration` fixture, a ``canaille.toml`` file,
environment variables prefixed by ``PYTEST_IAM_``, and a ``.pytest-iam.env`` file.
:doc:`configuration` lists them by priority.

The prefix keeps the server away from the ``CANAILLE_*`` variables that the tested project may use for its own needs.
The ``canaille.toml`` file is read by Canaille itself, and pytest-iam cannot disable it.
A project that has such a file at its root, or that sets ``CANAILLE_CONFIG``,
also configures the pytest-iam server with it.

:func:`~pytest_iam.iam_configuration` also sets the ``AUTHLIB_INSECURE_TRANSPORT`` environment variable,
so that `Authlib <https://authlib.org>`_ accepts the plain HTTP URLs of the server.
This variable applies to the whole test process,
including the Authlib clients of the tested application.

Logging
-------

Canaille logs with the ``canaille`` logger.
pytest-iam sets this logger to the ``DEBUG`` level and attaches a :class:`logging.NullHandler` to it.
The records still propagate to the root logger,
so :ref:`caplog <pytest:logging>` captures them,
and pytest shows them in the report of failing tests.
pytest-iam leaves the root logger and the loggers of the tested project untouched.

The access log of the HTTP server is disabled by default.
Set :attr:`~pytest_iam.Server.logging` to ``True`` to print one line per request on the standard error output.
