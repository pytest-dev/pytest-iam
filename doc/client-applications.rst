Test a client application
=========================

This guide shows how to test the login of a client application against the pytest-iam server.
It is meant for developers of an application that logs its users in with OAuth2 or OpenID Connect.
The examples use the ``user`` and ``client`` fixtures from :doc:`test-data`.
For applications that sign their authorization requests, see :doc:`signed-authorization-requests`.

Configure the application
-------------------------

The tested application uses :attr:`iam_server.url <pytest_iam.Server.url>` as its identity provider,
with the credentials of the ``client`` fixture.
The examples of this page use a Flask application with an `Authlib <https://authlib.org>`_ client:

- ``/protected`` redirects anonymous users to the IAM server, and greets logged in users;
- ``/create`` redirects to the IAM server, to create an account;
- ``/authorize`` exchanges the authorization code for a token, and stores the user in the session.

.. literalinclude:: examples/test_client_applications.py
    :language: python
    :start-at: import uuid
    :end-at: return app.test_client()

In a real project, the ``app`` fixture creates the tested application with the same settings.

Test the login
--------------

The test drives the application and the IAM server with their test clients.
It follows each redirection by hand, and fills the login, password and consent forms of the IAM server.

.. literalinclude:: examples/test_client_applications.py
    :language: python
    :pyobject: test_login

Skip the login and consent pages
--------------------------------

:meth:`~pytest_iam.Server.login` opens a session for a user on the IAM server,
and :meth:`~pytest_iam.Server.consent` records the consent of a user for a client.
The IAM server then answers the authorization request with a code at once.
The session ends with the test.

.. literalinclude:: examples/test_client_applications.py
    :language: python
    :pyobject: test_login_shortcuts

Test the account creation
-------------------------

The ``prompt=create`` parameter of the authorization request makes the IAM server show its registration form,
as defined by `Initiating User Registration via OpenID Connect 1.0 <https://openid.net/specs/openid-connect-prompt-create-1_0.html>`_.
The ``/create`` page of the application sends this parameter.

.. literalinclude:: examples/test_client_applications.py
    :language: python
    :pyobject: test_account_creation

pytest-iam has no shortcut for the account creation.
