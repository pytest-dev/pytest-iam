Client applications
===================

If you are writing a client application, you will probably want to test the nominal authentication case,
i.e. the case when the users successfully logs in and give their consent to your application.
Depending on your implementation, you might also need to test how your application behaves in case
of error during the authentication process.

You can also test how your application deals with OIDC registration or refresh token exchange.

pytest-iam will help you set up some of those scenarios in your tests.

Setting up your test
--------------------

Users & groups
~~~~~~~~~~~~~~

You can use the available :class:`~canaille.core.models.User` and :class:`~canaille.core.models.Group` models to set up their
IAM server for your tests. Optionally you can put them in pytest fixtures so they are reusable:


.. code:: python

    @pytest.fixture
    def user(iam_server):
        user = iam_server.models.User(
            user_name="user",
            emails=["email@example.org"],
            password="password",
        )
        iam_server.backend.save(user)
        yield user
        iam_server.backend.delete(user)

    @pytest.fixture
    def group(iam_server, user):
        group = iam_server.models.Group(
            display_name="group",
            members=[user],
        )
        iam_server.backend.save(group)
        yield group
        iam_server.backend.delete(group)

If you don't care about the data your users and group, you can use the available random generation utilities.

.. code:: python

    @pytest.fixture
    def user(iam_server):
        user = iam_server.random_user()
        iam_server.backend.save(user)
        yield user
        iam_server.backend.delete(user)

    @pytest.fixture
    def group(iam_server, user):
        group = iam_server.random_group()
        group.members = group.members + [user]
        iam_server.backend.save(group)
        yield group
        iam_server.backend.delete(group)

OIDC Client registration
~~~~~~~~~~~~~~~~~~~~~~~~

Before your application can authenticate against the IAM server, it must register and give provide details
such as the allowed redirection URIs. To achieve this you can use the :class:`~canaille.oidc.models.Client`
model. Let us suppose your application have a ``/authorize`` endpoint for the authorization code - token exchange:

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
        iam_server.backend.save(inst)
        yield inst
        iam_server.backend.delete(inst)

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

Nominal authentication case
---------------------------

Let us suppose that your application have a ``/protected`` that redirects users
to the IAM server if unauthenticated. With your :class:`~canaille.core.models.User`
and :class:`~canaille.oidc.models.Client` fixtures, you can use the
:meth:`~pytest_iam.Server.login` and :meth:`~pytest_iam.Server.consent` methods
to skip the login and the consent page from the IAM.

We suppose you have a test client fixture like werkzeug :class:`~werkzeug.test.Client`
that allows to test your application endpoints without real HTTP requests. Let
us see how to implement an authorization_code authentication test case:

.. code:: python

    def test_login_and_consent(iam_server, client, user, testclient):
        iam_server.login(user)
        iam_server.consent(user)

        # 1. attempt to access a protected page
        res = testclient.get("/protected", status=302)

        # 2. authorization code request
        res = requests.get(res.location, allow_redirects=False)

        # 3. load your application authorization endpoint
        res = testclient.get(res.headers["Location"], status=302)

        # 4. redirect to the protected page
        res = res.follow(status=200)

What happened?

1. A simulation of an access to a protected page on your application.
2. That redirects to the IAM authorization endpoint. Since the users are already
   logged and their consent already given, the IAM redirects to your application
   authorization configured redirect_uri, with the authorization code passed in
   the query string. Note that ``requests`` is used in this example to perform
   the request. Indeed, generally testclient such as the werkzeug one cannot
   perform real HTTP requests.
3. Access your application authorization endpoint that will exchange the
   authorization code against a token and check the user credentials.
4. For instance, your application can redirect the users back to the page
   they attempted to access in the first place.

Error cases
-----------

The `OAuth2 <https://datatracker.ietf.org/doc/html/rfc6749>`_ and the `OpenID Connect <https://openid.net/specs/openid-connect-core-1_0.html>`_ specifications details how things might go wrong:

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
