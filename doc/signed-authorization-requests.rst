Test signed authorization requests
==================================

This guide shows how to test a client application that sends its authorization requests
as signed request objects, as defined by `RFC 9101 (JAR) <https://www.rfc-editor.org/rfc/rfc9101>`_.
It is meant for developers who already test the authentication of their application with pytest-iam,
as described in :doc:`client-applications`.
It covers request objects sent by value, with the ``request`` parameter,
request objects sent by reference, with the ``request_uri`` parameter,
and clients that publish their keys on a URL.

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
The IAM server then downloads the keys from this URL.
:meth:`~pytest_iam.Server.mount` serves these downloads with a WSGI application, without network.
In a real test, mount the tested application.
The following example mounts a small application that only serves the keys:

.. literalinclude:: examples/test_signed_authorization_requests.py
    :language: python
    :pyobject: jwks_uri_client

The IAM server keeps the downloaded keys for 50 seconds for each ``client_id``.
A test that changes the keys of a client must use a new ``client_id``.

The tested application can also serve its keys with a real HTTP server,
for instance with the ``live_server`` fixture of pytest-flask or pytest-django.
The tested application may call the IAM server while it handles a request,
for instance to exchange a code with ``private_key_jwt`` authentication.
The IAM server then downloads the keys from the application, before it answers.
If the server of the application handles one request at a time, it cannot serve the keys.
The download fails after 5 seconds, and the IAM server rejects the request.
Use a multi-threaded server for the application, or :meth:`~pytest_iam.Server.mount`.

Send request objects by reference
---------------------------------

With the ``request_uri`` parameter, the client sends the URL of its request object instead of the request object.
The IAM server downloads the request object from this URL.
The client must register the URL in its ``request_uris``.
As for the keys, :meth:`~pytest_iam.Server.mount` serves the download.

.. literalinclude:: examples/test_signed_authorization_requests.py
    :language: python
    :pyobject: test_request_object_by_reference

The IAM server answers a ``request_uri`` that the client did not register with a ``400`` status.

.. literalinclude:: examples/test_signed_authorization_requests.py
    :language: python
    :pyobject: test_unregistered_request_uri_is_rejected
