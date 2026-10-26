Signed authorization requests
=============================

This guide shows how to test a client application that sends its authorization requests
as signed request objects, as defined by `RFC 9101 (JAR) <https://www.rfc-editor.org/rfc/rfc9101>`_.
It is meant for developers who already test the authentication of their application with pytest-iam,
as described in :doc:`client-applications`.
It covers request objects sent by value, with the ``request`` parameter.
Request objects sent by reference, with the ``request_uri`` parameter, have extra constraints,
described in :ref:`request-uri`.

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

.. _request-uri:

Request objects sent by reference
---------------------------------

With the ``request_uri`` parameter, the IAM server downloads the request object
with a real HTTP request, from the thread where it runs.
The tested application must then serve the request object on a URL that this thread can reach,
for instance with a local HTTP server.
A Werkzeug or Flask test client is not enough, because it does not listen on the network.

The same constraint applies to a client that publishes its keys with ``jwks_uri`` instead of ``jwks``.
