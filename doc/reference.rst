Reference
#########

This page lists the fixtures and the classes of pytest-iam.

Fixtures
========

.. autofunction:: pytest_iam.iam_server() -> pytest_iam.Server

.. autofunction:: pytest_iam.iam_configuration() -> dict

.. autofunction:: pytest_iam.iam_server_port() -> int

.. autofunction:: pytest_iam.iam_restore_login()

Server
======

.. autoclass:: pytest_iam.Server()
    :members:
    :undoc-members:
    :member-order: groupwise
    :exclude-members: httpd

Models
======

:attr:`Server.models <pytest_iam.Server.models>` gives access to the Canaille models,
documented in :doc:`canaille:references/models`:

- :class:`~canaille.core.models.User`
- :class:`~canaille.core.models.Group`
- :class:`~canaille.core.models.WebAuthnCredential`
- :class:`~canaille.oidc.basemodels.Client`
- :class:`~canaille.oidc.basemodels.AuthorizationCode`
- :class:`~canaille.oidc.basemodels.Token`
- :class:`~canaille.oidc.basemodels.Consent`
