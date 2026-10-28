pytest-iam
==========

pytest-iam is a pytest plugin that starts an OAuth2, OpenID Connect (OIDC) and SCIM server for the tests of an application.
The server is a [Canaille](https://canaille.readthedocs.io) instance, built on [Authlib](https://authlib.org).

- [Documentation](https://pytest-iam.readthedocs.io)
- [Repository](https://github.com/pytest-dev/pytest-iam)
- [Issues](https://github.com/pytest-dev/pytest-iam/issues)
- [Package](https://pypi.org/project/pytest-iam)

Why pytest-iam
--------------

A mock of the identity provider only gives the answers that the test expects.
pytest-iam runs a real IAM server instead,
so the tests go through the real OAuth2 and OIDC flows: redirections, forms, code exchange and token introspection.
SCIM applications send their requests to a real SCIM API.
The server runs in a thread of the test process.
It needs no container, and it only listens on `localhost`.

Installation
------------

```console
uv add --dev pytest-iam
```

The SCIM API needs the `scim` extra:

```console
uv add --dev "pytest-iam[scim]"
```

Usage
-----

The `iam_server` fixture gives access to the IAM server:

- its URL, to configure the tested application;
- its SCIM API at `/scim/v2`, with the `scim` extra;
- its models, such as users, groups, clients and tokens, to prepare the tests and check their effects;
- shortcuts to log users in and record their consent;
- helpers to create random users, groups and tokens.

The following test logs a user in on a client application.
The `client` fixture registers the application on the IAM server, and the `user` fixture creates a user,
as described in [the test data guide](https://pytest-iam.readthedocs.io/en/latest/test-data.html).
`test_client` is the test client of the application.

```python
def test_login_shortcuts(iam_server, client, user, test_client):
    iam_server.login(user)
    iam_server.consent(user, client)

    # 1. the protected page redirects to the IAM server
    res = test_client.get("/protected")

    # 2. the IAM server redirects to the application with a code
    res = iam_server.test_client.get(res.location)

    # 3. the application exchanges the code for a token
    res = test_client.get(res.location)

    # 4. the protected page is now accessible
    res = test_client.get(res.location)
    assert res.text == "Hello, user!"
```

The [documentation](https://pytest-iam.readthedocs.io) has guides for client applications, resource servers, signed authorization requests and SCIM applications.

License
-------

pytest-iam is published under the MIT license.
