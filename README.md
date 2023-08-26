pytest-iam
==========

pytest-iam spawns a lightweight OAuth2 / OpenID Server (OIDC) in a thread to be used in your test suite.
The machinery involves [Canaille](https://canaille.yaal.coop) and [Authlib](https://authlib.org).

- [Repository](https://gitlab.com/yaal-coop/pytest-iam)
- [Package](https://pypi.org/project/pytest-iam)
- [Documentation](https://pytest-iam.readthedocs.io)

Installation
------------

```console
pip install pytest-iam
```

Usage
-----

pytest-iam provides tools to test your application authentication mechanism agaist a OAuth2/OIDC server:

- It launches a [Canaille](https://canaille.yaal.coop) instance
- It provides a ``iam_server`` fixture that comes with several features:
    - the URL of the IAM server to configure your application
    - IAM models (Users, groups, clients, tokens etc.) to prepare your tests and check the side effects.
      More details on [the reference](https://pytest-iam.readthedocs.io/en/latest/reference.html)
    - utilities to log-in users and give their consent to your application
    - utilities to generate random users and groups

To run a full authentication process for a client application in your test,
you can write something like this:

```python
def test_authentication(iam_server, testapp, client):
    # create a random user on the IAM server
    user = iam_server.random_user()

    # logs the user in give its consent to your application
    iam_server.login(user)
    iam_server.consent(user)

    # simulate an attempt to access a protected page of your app
    response = testapp.get("/protected", status=302)

    # get an authorization code request at the IAM
    res = requests.get(res.location, allow_redirects=False)

    # access to the redirection URI
    res = testclient.get(res.headers["Location"])
    res.mustcontain("Hello World!")
```

Check the [client application](https://pytest-iam.readthedocs.io/en/latest/client-applications.html) or
[resource server](https://pytest-iam.readthedocs.io/en/latest/resource-servers.html) tutorials
for more usecases.
