Signed authorization requests
=============================

This guide shows how to test a client application that sends its authorization requests
as signed request objects, as defined by `RFC 9101 (JAR) <https://www.rfc-editor.org/rfc/rfc9101>`_.
It is meant for developers who already test the authentication of their application with pytest-iam,
as described in :doc:`client-applications`.
It covers request objects sent by value, with the ``request`` parameter,
and clients that publish their keys on a URL.
It does not cover request objects sent by reference, with the ``request_uri`` parameter:
see :ref:`request-uri`.

Register the client keys
------------------------

The IAM server checks the request object signature with the public keys of the client.
Register these keys in the ``jwks`` attribute of the client, as a JSON string.
Set ``require_signed_request_object`` to reject the authorization requests that are not signed.

.. literalinclude:: examples/test_signed_authorization_requests.py
    :language: python
    :start-at: import json
    :end-at: iam_server.backend.delete(client)

Configure the tested application to sign its request objects with ``client_key``.

Check that the signed request is accepted
-----------------------------------------

The IAM server answers a valid signed request with a redirection to the client,
carrying an authorization code.
In the following example, the test builds the request object itself.
In a real test, the tested application builds it,
and the test passes the redirection of the application to the IAM server.

.. literalinclude:: examples/test_signed_authorization_requests.py
    :language: python
    :pyobject: test_signed_request_object

Check that unsigned requests are rejected
-----------------------------------------

With ``require_signed_request_object``, the IAM server answers a plain authorization request
with a ``400`` status.
The same status applies to a request object signed with a key that the client did not register.
A test on this case checks that the tested application never falls back to plain requests.

.. literalinclude:: examples/test_signed_authorization_requests.py
    :language: python
    :pyobject: test_unsigned_request_is_rejected

Serve the client keys on a URL
------------------------------

A client can publish its keys on a URL with ``jwks_uri``, instead of storing them in ``jwks``.
The IAM server then downloads the keys with a real HTTP request.
A Werkzeug or Flask test client is not enough to serve them,
because it does not listen on the network.
Start an HTTP server in the test process instead, for instance with :mod:`wsgiref`:

.. literalinclude:: examples/test_signed_authorization_requests.py
    :language: python
    :pyobject: jwks_url

Then set ``jwks_uri=jwks_url`` on the client, instead of ``jwks``.
The tested application can also serve its own keys,
for instance with the ``live_server`` fixture of pytest-flask or pytest-django.

The IAM server keeps the downloaded keys for 50 seconds for each ``client_id``.
A test that changes the keys of a client must use a new ``client_id``.

The tested application may call the IAM server while it handles a request,
for instance to exchange a code with ``private_key_jwt`` authentication.
The IAM server then downloads the keys from the application, before it answers.
If the server of the application handles one request at a time, it cannot serve the keys.
With Canaille 0.3.0, the download fails after 5 seconds, and the IAM server answers with a ``500`` status.
Serve the keys from a separate server, or use a multi-threaded server for the application.

.. _request-uri:

Request objects sent by reference
---------------------------------

Canaille 0.3.0 rejects every authorization request with a ``request_uri`` parameter,
with a ``400`` status.
