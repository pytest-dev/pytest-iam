pytest-iam
==========

pytest-iam spawns a lightweight OAuth2 / OpenID Server (OIDC) / SCIM in a thread to be used in your test suite.
The machinery involves [Canaille](https://canaille.readthedocs.io) and [Authlib](https://authlib.org).

- [Repository](https://github.com/pytest-dev/pytest-iam)
- [Package](https://pypi.org/project/pytest-iam)
- [Documentation](https://pytest-iam.readthedocs.io)

Installation
------------

```console
uv add pytest-iam
```

Usage
-----

pytest-iam provides tools to test your application authentication mechanism against a OAuth2/OIDC server, with SCIM support:

- It launches a [Canaille](https://canaille.readthedocs.io) instance on a random port;
- It provides a ``iam_server`` fixture that comes with several features:
    - the URL of the IAM server to configure your application
    - IAM models (Users, groups, clients, tokens etc.) to prepare your tests and check the side effects.
      More details on [the reference](https://pytest-iam.readthedocs.io/en/latest/reference.html)
    - utilities to log-in users and give their consent to your application
    - utilities to generate random users and groups

To run a full authentication process for a client application in your test,
you can write something like this:

```python
def test_authentication(iam_server, test_client):
    # create a random user on the IAM server
    user = iam_server.random_user()

    # log the user in and make it consent all the clients
    iam_server.login(user)
    iam_server.consent(user)

    # 1. attempt to access a protected page, returns a redirection to the IAM
    res = test_client.get("/protected")

    # 2. authorization code request
    res = iam_server.test_client.get(res.location)

    # 3. load your application authorization endpoint
    res = test_client.get(res.location)

    # 4. now you have access to the protected page
    res = test_client.get("/protected")

    assert "Hello, world!" in res.text
```

Check the [client application](https://pytest-iam.readthedocs.io/en/latest/client-applications.html) or
[resource server](https://pytest-iam.readthedocs.io/en/latest/resource-servers.html) tutorials
for more usecases.
