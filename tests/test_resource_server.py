import uuid

import joserfc.jwk
import joserfc.jwt
import pytest
import requests
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc7662 import IntrospectTokenValidator
from flask import current_app
from flask import Flask


@pytest.fixture
def app(iam_server, client):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = str(uuid.uuid4())
    app.config["SERVER_NAME"] = "example.org"
    app.config["TOKEN_TYPE"] = "plain"

    class TokenValidator(IntrospectTokenValidator):
        def introspect_token(self, token_string):
            server_metadata = requests.get(
                f"{iam_server.url}.well-known/openid-configuration"
            ).json()

            if current_app.config.get("TOKEN_TYPE") == "jwt":
                return self.check_jwt_token(server_metadata, token_string)
            return self.check_plain_token(server_metadata, token_string)

        def check_plain_token(self, server_metadata, token_string):
            data = {"token": token_string, "token_type_hint": "access_token"}
            auth = (client.client_id, client.client_secret)
            resp = requests.post(
                server_metadata.get("introspection_endpoint"), data=data, auth=auth
            )
            resp.raise_for_status()
            return resp.json()

        def check_jwt_token(self, server_metadata, token_string):
            url = server_metadata.get("jwks_uri")
            resp = requests.get(url)
            key_set = joserfc.jwk.KeySet.import_key_set(resp.json())

            try:
                print(joserfc.jwt.decode(token_string, key_set).claims)
                return joserfc.jwt.decode(token_string, key_set).claims
            except ValueError:
                return None

    require_oauth = ResourceProtector()
    require_oauth.register_token_validator(TokenValidator())

    @app.route("/resource")
    @require_oauth("profile")
    def login():
        return {"success": True}

    return app


@pytest.fixture
def testclient(app):
    app.config["TESTING"] = True
    return app.test_client()


def test_valid_plain_token_auth(iam_server, testclient, client, user):
    testclient.application.config["TOKEN_TYPE"] = "plain"
    token = iam_server.random_token(
        client=client, subject=user, access_token=str(uuid.uuid4())
    )
    res = testclient.get(
        "/resource", headers={"Authorization": f"Bearer {token.access_token}"}
    )
    assert res.status_code == 200
    assert res.json["success"]


def test_invalid_plaint_token_auth(iam_server, testclient):
    testclient.application.config["TOKEN_TYPE"] = "plain"
    res = testclient.get("/resource", headers={"Authorization": "Bearer invalid"})
    assert res.status_code == 401


def test_valid_token_jwt_auth(iam_server, testclient, client, user):
    testclient.application.config["TOKEN_TYPE"] = "jwt"
    token = iam_server.random_token(client=client, subject=user)
    res = testclient.get(
        "/resource", headers={"Authorization": f"Bearer {token.access_token}"}
    )
    assert res.status_code == 200
    assert res.json["success"]


def test_invalid_jwt_token_auth(iam_server, testclient, client, user):
    testclient.application.config["TOKEN_TYPE"] = "jwt"
    token = iam_server.random_token(client=client, subject=user)
    access_token = token.access_token
    token.delete()

    res = testclient.get(
        "/resource", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert res.status_code == 200
    assert res.json["success"]
