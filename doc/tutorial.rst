Tutorial
========

What to test?
-------------

You will probably want to test the nominal authentication case for your application, i.e. the case when the users successfully logs in and give their consent to your application.
However, the `OAuth2 <https://datatracker.ietf.org/doc/html/rfc6749>`_ and the `OpenID Connect <https://openid.net/specs/openid-connect-core-1_0.html>`_ specifications details how things might go wrong:

The `OAuth2 error codes <https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.2.1>`_:

- invalid_request
- unauthorized_client
- access_denied
- unsupported_response_type
- invalid_scope
- server_error
- temporarily_unavailable

The `OIDC error codes <https://openid.net/specs/openid-connect-core-1_0.html#AuthError>`_:

- interaction_required
- login_required
- account_selection_required
- consent_required
- invalid_request_uri
- invalid_request_object
- request_not_supported
- request_uri_not_supported
- registration_not_supported

You might or might not be interested in testing how your application behaves when it encounters those situations,
depending on the situation and how much you trust the libraries that helps your application perform the authentication process.
pytest-iam will help you set up some of those scenarios in your tests

Setting up your test
--------------------

Users & groups
~~~~~~~~~~~~~~

You can use the available :class:`~canaille.core.models.User` and :class:`~canaille.core.models.Group` models to set up their
IAM server for your tests. Optionnally you can put them in pytest fixtures so they are re-usable:


.. code:: python

    @pytest.fixture
    def user(iam_server):
        user = iam_server.models.User(
            user_name="user",
            emails=["email@example.org"],
            password="password",
        )
        user.save()
        yield user
        user.delete()

    @pytest.fixture
    def group(iam_server, user):
        group = iam_server.models.Group(
            display_name="group",
            members=[user],
        )
        group.save()
        yield group
        group.delete()

If you don't care about the data your users and group, you can use the available random generation utilities.

.. code:: python

    @pytest.fixture
    def user(iam_server):
        user = iam_server.random_user()
        user.save()
        yield user
        user.delete()

    @pytest.fixture
    def group(iam_server, user):
        group = iam_server.random_group()
        group.members = group.members + [user]
        group.save()
        yield group
        group.delete()

OIDC Client
~~~~~~~~~~~

Before your application can authenticate against the IAM server, it must register and give provide details
such as the allowed redirection URIs. To achieve this you can use the :class:`~canaille.core.models.Client`
model:

.. code:: python

    @pytest.fixture
    def client(iam_server):
        inst = iam_server.models.Client(
            client_id="client_id",
            client_secret="client_secret",
            client_name="My Application",
            client_uri="http://example.org",
            redirect_uris=["http://example.org/authorize"],
            grant_types=["authorization_code"],
            response_types=["code", "token", "id_token"],
            token_endpoint_auth_method="client_secret_basic",
            scope=["openid", "profile", "groups"],
        )
        inst.save()
        yield inst
        inst.delete()

Note that the IAM implements the `OAuth2/OIDC dynamic client registration protocol <https://datatracker.ietf.org/doc/html/rfc7591>`_,
thus you might not need a client fixture if your application dynamically register one. No *initial token* is needed to use dynamic
client registration. Here is an example of dynamic registration you can implement in your application:

.. code:: python

    response = requests.post(
        f"{iam_server.url}/oauth/register",
        json={
            "client_name": "My application",
            "client_uri": "http://example.org",
            "redirect_uris": ["http://example.org/authorize"],
            "grant_types": ["authorization_code"],
            "response_types": ["code", "token", "id_token"],
            "token_endpoint_auth_method": "client_secret_basic",
            "scope": "openid profile groups",
        },
    )
    client_id = response.json()["client_id"]
    client_secret = response.json()["client_secret"]
