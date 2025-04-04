import uuid

import pytest
import requests
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask import jsonify
from flask import url_for


def test_server_configuration(iam_server):
    res = requests.get(f"{iam_server.url}/.well-known/openid-configuration")
    assert res.json()["issuer"] in iam_server.url


def test_client_dynamic_registration(iam_server):
    response = requests.post(
        f"{iam_server.url}/oauth/register",
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
    client_id = response.json()["client_id"]
    client_secret = response.json()["client_secret"]

    client = iam_server.backend.get(iam_server.models.Client, client_id=client_id)
    assert client.client_secret == client_secret
    iam_server.backend.delete(client)


def test_logs(iam_server, caplog):
    response = requests.post(
        f"{iam_server.url}/oauth/register",
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

    client_id = response.json()["client_id"]
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

    @app.route("/authorize")
    def authorize():
        token = oauth.authorization_server.authorize_access_token()
        return jsonify(token)

    return app


@pytest.fixture
def testclient(app):
    app.config["TESTING"] = True
    return app.test_client()


def test_login_and_consent(iam_server, client, user, testclient):
    iam_server.login(user)
    iam_server.consent(user)

    # attempt to access a protected page
    res = testclient.get("/login")

    # authorization code request (already logged in an consented)
    res = requests.get(res.location, allow_redirects=False)

    authorization = iam_server.backend.get(iam_server.models.AuthorizationCode)
    assert authorization.client == client

    res = testclient.get(res.headers["Location"])

    token = iam_server.backend.get(iam_server.models.Token)
    assert token.client == client

    assert res.json["userinfo"]["sub"] == "user"
    assert res.json["access_token"] == token.access_token
