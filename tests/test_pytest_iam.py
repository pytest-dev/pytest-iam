import uuid

import pytest
import requests
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask import jsonify
from flask import url_for


def test_server_configuration(iam_server):
    res = requests.get(f"{iam_server.url}/.well-known/openid-configuration")
    assert res.json()["issuer"] == iam_server.url


def test_client_registration(iam_server):
    response = requests.post(
        f"{iam_server.url}/oauth/register",
        json={
            "client_name": "Nubla Dashboard",
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

    client = iam_server.models.Client.get(client_id=client_id)
    assert client.client_secret == client_secret


@pytest.fixture
def client(iam_server):
    inst = iam_server.models.Client(
        client_id="client_id",
        client_secret="client_secret",
        client_name="Nubla Dashboard",
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


@pytest.fixture
def user(iam_server):
    inst = iam_server.models.User(
        user_name="user",
        emails=["email@example.org"],
        password="password",
    )
    inst.save()
    yield inst
    inst.delete()


def test_authlib_integration(iam_server, client, user):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = str(uuid.uuid4())
    app.config["SERVER_NAME"] = "example.org"

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

    @app.route("/authorize")
    def authorize():
        token = oauth.authorization_server.authorize_access_token()
        return jsonify(token)

    testclient = app.test_client()
    redirect_uri = testclient.get("/login").location

    s = requests.Session()

    # login screen
    res = s.post(
        redirect_uri,
        data={
            "login": "user",
            "password": "password",
        },
        allow_redirects=False,
    )

    # consent screen
    res = s.post(
        redirect_uri,
        data={"answer": "accept"},
        allow_redirects=False,
    )

    authorization = iam_server.models.AuthorizationCode.get()
    assert authorization.client == client

    res = testclient.get(res.headers["Location"])

    token = iam_server.models.Token.get()
    assert token.client == client

    assert res.json["userinfo"]["sub"] == "user"
    assert res.json["access_token"] == token.access_token