import uuid

import pytest
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask import jsonify
from flask import url_for


def test_server_configuration(iam_server):
    res = iam_server.test_client.get("/.well-known/openid-configuration")
    assert res.json["issuer"] in iam_server.url


def test_client_dynamic_registration(iam_server):
    response = iam_server.test_client.post(
        "/oauth/register",
        json={
            "client_name": "Nubla Dashboard",
            "client_uri": "http://client.test",
            "redirect_uris": ["http://client.test/authorize"],
            "grant_types": ["authorization_code"],
            "response_types": ["code", "token", "id_token"],
            "token_endpoint_auth_method": "client_secret_basic",
            "scope": "openid profile groups",
        },
    )
    client_id = response.json["client_id"]
    client_secret = response.json["client_secret"]

    client = iam_server.backend.get(iam_server.models.Client, client_id=client_id)
    assert client.client_secret == client_secret
    iam_server.backend.delete(client)


def test_logs(iam_server, caplog):
    response = iam_server.test_client.post(
        "/oauth/register",
        json={
            "client_name": "Nubla Dashboard",
            "client_uri": "http://client.test",
            "redirect_uris": ["http://client.test/authorize"],
            "grant_types": ["authorization_code"],
            "response_types": ["code", "token", "id_token"],
            "token_endpoint_auth_method": "client_secret_basic",
            "scope": "openid profile groups",
        },
    )

    assert caplog.records[0].msg == "client registration endpoint request: POST: %s"

    client_id = response.json["client_id"]
    client = iam_server.backend.get(iam_server.models.Client, client_id=client_id)
    iam_server.backend.delete(client)


@pytest.fixture
def app(iam_server, client):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = str(uuid.uuid4())
    app.config["SERVER_NAME"] = "client.test"

    oauth = OAuth()
    oauth.init_app(app)
    oauth.register(
        name="authorization_server",
        client_id=client.client_id,
        client_secret=client.client_secret,
        server_metadata_url=f"{iam_server.url}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile groups"},
    )

    @app.route("/login")
    def login():
        return oauth.authorization_server.authorize_redirect(
            url_for("authorize", _external=True)
        )

    @app.route("/create")
    def create():
        return oauth.authorization_server.authorize_redirect(
            url_for("authorize", _external=True), prompt="create"
        )

    @app.route("/authorize")
    def authorize():
        token = oauth.authorization_server.authorize_access_token()
        return jsonify(token)

    return app


@pytest.fixture
def test_client(app):
    app.config["TESTING"] = True
    return app.test_client()


def test_login_and_consent(iam_server, client, user, test_client):
    # 1. attempt to access a protected page
    res = test_client.get("/login")

    # 2. redirect to the authorization server login page
    res = iam_server.test_client.get(res.location)

    # 3. fill the 'login' form
    res = iam_server.test_client.post(res.location, data={"login": "user"})

    # 4. fill the 'password' form
    res = iam_server.test_client.post(
        res.location, data={"password": "correct horse battery staple"}
    )

    # 5. fill the 'consent' form
    res = iam_server.test_client.post(res.location, data={"answer": "accept"})

    authorization = iam_server.backend.get(iam_server.models.AuthorizationCode)
    assert authorization.client == client

    # 6. load your application authorization endpoint
    res = test_client.get(res.location)

    token = iam_server.backend.get(iam_server.models.Token)
    assert token.client == client

    assert res.json["userinfo"]["sub"] == "user"
    assert res.json["access_token"] == token.access_token

    iam_server.logout()


def test_prelogin_and_preconsent(iam_server, client, user, test_client):
    iam_server.login(user)
    iam_server.consent(user)

    # attempt to access a protected page
    res = test_client.get("/login")

    # authorization code request (already logged in an consented)
    res = iam_server.test_client.get(res.location)

    authorization = iam_server.backend.get(iam_server.models.AuthorizationCode)
    assert authorization.client == client

    # return to the client with a code
    res = test_client.get(res.location)

    iam_server.logout()


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
        "preferred_language": "auto",  # appears to be mandatory
        "password1": "correct horse battery staple",
        "password2": "correct horse battery staple",
    }

    # fill the registration form
    res = iam_server.test_client.post(res.location, data=payload)

    # fill the 'consent' form
    res = iam_server.test_client.post(res.location, data={"answer": "accept"})

    authorization = iam_server.backend.get(iam_server.models.AuthorizationCode)
    assert authorization.client == client

    # return to the client with a code
    res = test_client.get(res.location)

    token = iam_server.backend.get(iam_server.models.Token)
    assert token.client == client

    assert res.json["userinfo"]["sub"] == "user"
    assert res.json["access_token"] == token.access_token

    user = iam_server.backend.get(iam_server.models.User)
    assert user.user_name == "user"

    iam_server.logout()
