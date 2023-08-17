pytest-iam
==========

pytest-iam spawns a lightweight OAuth2 / OpenID Server in a thread to be used in your test suite.
The machinery involves [Canaille](https://canaille.yaal.coop) and [Authlib](https://authlib.org).

Installation
------------

```console
pip install pytest-iam
```

Usage
-----

pytest-iam provides a ``iam_server`` fixture that comes with several features:

- ``iam_server.url`` returns the temporary server url
- ``iam_server.models`` provides a modules containing different models (``User``, ``Group``, ``Client``, ``Token`` and ``AuthorizationCode``). Read the [canaille documentation](https://canaille.readthedocs.io/en/latest/reference.html) to find how to handle those models.
- ``iam_server.random_user()`` and ``iam_server.random_group()`` can generate random data for your tests

To run a full authentication process in your test, you can write something like this:

```python
# We suppose you want to test a Flask application
def test_authentication(iam_server, testapp, client, user):
    s = requests.Session()

    # The /protected URL is protected and redirects to the identity provider
    redirect_uri = testapp.get("/protected", status=302).location

    # The IdP presents a login screen
    res = s.post(
        redirect_uri,
        data={
            "login": "user",
            "password": "password",
        },
        allow_redirects=False,
    )

    # The IdP presents a consent screen
    res = s.post(
        redirect_uri,
        data={"answer": "accept"},
        allow_redirects=False,
    )

    # The IdP redirects to the client authorization endpoint
    res = testapp.get(res.headers["Location"])

    # Then the client endpoint finnaly redirects to the initial /protected page
    res = res.follow()
    res.mustcontain("Hello World!")
```
