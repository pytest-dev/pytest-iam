Test a SCIM application
=======================

This guide shows how to test an application that reads or writes the users and groups of the IAM server
with the `SCIM <https://www.rfc-editor.org/rfc/rfc7644>`_ API.
It is meant for developers of provisioning applications.
The examples use `scim2-client <https://scim2-client.readthedocs.io>`_.
It does not cover the SCIM client of Canaille, which sends the user changes to other applications.

Install the SCIM extra
----------------------

The SCIM API needs the ``scim`` extra of pytest-iam:

.. code-block:: console

    uv add --dev "pytest-iam[scim]"

Without this extra, the IAM server answers the SCIM requests with a ``404`` status.

Give the application a token
----------------------------

The SCIM API of the IAM server is at ``f"{iam_server.url}scim/v2"``.
Its requests need a bearer token.
A client token needs one of these scopes:

- ``scim:read`` or ``scim:write``, for users and groups;
- ``scim:users:read`` or ``scim:users:write``, for users only;
- ``scim:groups:read`` or ``scim:groups:write``, for groups only.

:meth:`~pytest_iam.Server.random_token` creates a token with the scopes of the client.
The following ``scim`` fixture sends the requests to the IAM server without network.
A tested application that sends HTTP requests can use the same URL and token.

.. literalinclude:: examples/test_scim.py
    :language: python
    :start-at: import pytest
    :end-at: return scim

A user token only gives access to the user itself, with the ``scim:me`` scope.

Create a user
-------------

The ``User`` schema of the IAM server requires ``name.formatted``, ``name.familyName`` and ``active``.
The test checks the created user in the database.

.. literalinclude:: examples/test_scim.py
    :language: python
    :pyobject: test_create_user

Check that a token needs a SCIM scope
-------------------------------------

The IAM server answers the requests with a token without SCIM scope with a ``403`` status.
scim2-client raises :class:`~scim2_models.ForbiddenException`.

.. literalinclude:: examples/test_scim.py
    :language: python
    :pyobject: test_token_without_scim_scope
