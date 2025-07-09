Client applications
===================

If you are writing a client application, you will probably want to test the nominal authentication case,
i.e. the case when the users successfully log in and give their consent to your application.
Depending on your implementation, you might also need to test how your application behaves in case
of error during the authentication process.

You can also test how your application deals with OIDC registration or refresh token exchange.

pytest-iam will help you set up some of those scenarios in your tests.

Setting up your test
--------------------

Start by configuring your application so it uses pytest-iam as identity provider.
This would probably be something in the fashion of:

.. code:: python
    :caption: conftest.py

    @pytest.fixture
    def app(iam_server):
        return create_app(
            config={
                "SERVER_NAME": "myclient.test",
                "SECRET_KEY": str(uuid.uuid4()),
                "OAUTH_SERVER": iam_server.url,
            }
        )

Users & groups
~~~~~~~~~~~~~~

You can use the available :class:`~canaille.core.models.User` and :class:`~canaille.core.models.Group` models to set up the
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

Before your application can authenticate against the IAM server, it must register and provide details
such as the allowed redirection URIs. To achieve this you can use the :class:`~canaille.oidc.basemodels.Client`
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

.. note::

   Clients have a :attr:`~canaille.oidc.basemodels.Client.trusted` parameter.
   When it is :data:`True`, end-users won't be showed a consent page
   when the client redirect them to the IAM authorization page.

Note that the IAM implements the `OAuth2/OIDC dynamic client registration protocol <https://datatracker.ietf.org/doc/html/rfc7591>`_,
thus you might not need a client fixture if your application dynamically register one. No *initial token* is needed to use dynamic
client registration. Here is an example of dynamic registration you can implement in your application:

.. code:: python

    response = iam_server.test_client.post(
        "/oauth/register",
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
    client_id = response.json["client_id"]
    client_secret = response.json["client_secret"]

Nominal authentication workflow
-------------------------------

Let us suppose that your application have a ``/protected`` endpoint that redirects users
to the IAM server if unauthenticated.
We suppose that you have a `test_client` fixture like werkzeug :class:`~werkzeug.test.Client`
that allows to test your application endpoints without real HTTP requests.
pytest-iam provides its own test client, available with :meth:`~pytest_iam.Server.test_client`.
Let us see how to implement an authorization_code authentication test case:

.. code-block:: python
   :caption: Full login and consent workflow to get an access token

    def test_login_and_consent(iam_server, client, user, test_client):
        # 1. attempt to access a protected page
        res = test_client.get("/protected")

        # 2. redirect to the authorization server login page
        res = iam_server.test_client.get(res.location)

        # 3. fill the 'login' form at the IAM
        res = iam_server.test_client.post(res.location, data={"login": "user"})

        # 4. fill the 'password' form at the IAM
        res = iam_server.test_client.post(
            res.location, data={"password": "correct horse battery staple"}
        )

        # 5. fill the 'consent' form at the IAM
        res = iam_server.test_client.post(res.location, data={"answer": "accept"})

        # 6. load your application authorization endpoint
        res = test_client.get(res.location)

        # 7. now you have access to the protected page
        res = test_client.get("/protected")

What happened?

1. A simulation of an access to a protected page on your application. As the page is protected,
   it returns a redirection to the IAM login page.
2. The IAM test client loads the login page and get redirected to the login form.
3. The login form is filled, and returns a redirection to the password form.
4. The password form is filled, and returns a redirection to the consent form.
5. The consent form is filled, and return a redirection to your application authorization endpoint with a OAuth code grant.
6. You client authorization endpoint is loaded, it reaches the IAM and exchanges the code grant with a token.   This is generally where you fill the session to keep users logged in.
7. The protected page is loaded, and now you should be able to access it.

Steps 2, 3 and 4 can be quite redundant, so pytest-iam provides shortcuts with the
:meth:`~pytest_iam.Server.login` and :meth:`~pytest_iam.Server.consent` methods.
They allow you to skip the login, password and consent pages:

.. code-block:: python
   :caption: Fast login and consent workflow to get an access token

    def test_login_and_consent(iam_server, client, user, test_client):
        iam_server.login(user)
        iam_server.consent(user)

        # 1. attempt to access a protected page
        res = test_client.get("/protected")

        # 2. authorization code request
        res = iam_server.test_client.get(res.location)

        # 3. load your application authorization endpoint
        res = test_client.get(res.location)

        # 4. now you have access to the protected page
        res = test_client.get("/protected")

Authentication workflow errors
------------------------------

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

Account creation workflow
-------------------------

The `Initiating User Registration via OpenID Connect 1.0 <https://openid.net/specs/openid-connect-prompt-create-1_0.html>`_
specification details how to initiate an account creation workflow at the IAM
by setting the ``prompt=create`` authorization request parameter.

In the following example, we suppose that the ``/create`` endpoint redirects
to the IAM authorization endpoint with the ``prompt=create`` parameters.

.. code-block:: python
    :caption: Account creation workflow

    def test_account_creation(iam_server, client, test_client):
        # access to the client account creation page
        res = test_client.get("/create")

        # redirection to the IAM account creation page
        res = iam_server.test_client.get(res.location)

        # redirection to the account creation page
        res = iam_server.test_client.get(res.location)

        payload = {
            "user_name": "user",
            "given_name": "John",
            "family_name": "Doe",
            "emails-0": "email@example.com",
            "preferred_language": "auto", # appears to be mandatory
            "password1": "correct horse battery staple",
            "password2": "correct horse battery staple",
        }

        # fill the registration form
        res = iam_server.test_client.post(res.location, data=payload)

        # fill the 'consent' form
        res = iam_server.test_client.post(res.location, data={"answer": "accept"})

        # return to the client with a code
        res = test_client.get(res.location)

        assert "User account successfully created" in res.text

Unfortunately there is no helpers for account creation in the fashion of :meth:`~pytest_iam.Server.login`.

Provisioning
------------

The ``iam_server`` instance provides a `SCIM2 provisioning API <https://scim.libre.sh>`_ at the address ``/scim/v2``.
You can use it to update your user profiles directly at the IAM.
You can have a look to the :doc:`Canaille documentation <canaille:tutorial/provisioning>` to see implementation details.

To perform SCIM requests you might be interested in tools such as `scim2-client <https://scim2-cli.readthedocs.io>`_.
