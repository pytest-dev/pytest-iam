Test a resource server
======================

This guide shows how to test a resource server that checks access tokens with the pytest-iam server.
It is meant for developers of an API that accepts OAuth2 bearer tokens.
It covers token introspection, as defined by `RFC 7662 <https://datatracker.ietf.org/doc/html/rfc7662>`_.
The examples use the ``user`` and ``client`` fixtures from :doc:`test-data`.
It does not cover JWT access tokens (`RFC 9068 <https://www.rfc-editor.org/rfc/rfc9068.html>`_):
:meth:`~pytest_iam.Server.random_token` creates opaque tokens only.

Configure the resource server
-----------------------------

The tested resource server sends each token to the introspection endpoint of the IAM server,
at ``oauth/introspect`` under :attr:`iam_server.url <pytest_iam.Server.url>`.
It authenticates with the credentials of the ``client`` fixture.
The examples of this page use a Flask application protected by Authlib.
Its ``/resource`` endpoint needs the ``profile`` scope.

.. literalinclude:: examples/test_resource_servers.py
    :language: python
    :start-at: import pytest
    :end-at: return app.test_client()

In a real project, the ``app`` fixture creates the tested resource server with the same settings.

Create access tokens
--------------------

:meth:`~pytest_iam.Server.random_token` creates a token for a client.
With a user as ``subject``, the token acts for this user.
With ``subject=None``, the token belongs to the client only, as with the client credentials grant.
The token has the scopes of the client, and lasts one hour.

.. literalinclude:: examples/test_resource_servers.py
    :language: python
    :pyobject: user_token

.. literalinclude:: examples/test_resource_servers.py
    :language: python
    :pyobject: client_token

Check the access
----------------

A valid token gives access to the resource:

.. literalinclude:: examples/test_resource_servers.py
    :language: python
    :pyobject: test_user_token

An unknown token gets a ``401`` status:

.. literalinclude:: examples/test_resource_servers.py
    :language: python
    :pyobject: test_invalid_token

Keyword arguments of :meth:`~pytest_iam.Server.random_token` change the token values.
A token without the ``profile`` scope gets a ``403`` status:

.. literalinclude:: examples/test_resource_servers.py
    :language: python
    :pyobject: test_missing_scope
