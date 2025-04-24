import uuid

import pytest
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc7662 import IntrospectTokenValidator
from flask import Flask


@pytest.fixture
def app(iam_server, client):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = str(uuid.uuid4())
    app.config["SERVER_NAME"] = "resource-server.test"

    class MyIntrospectTokenValidator(IntrospectTokenValidator):
        def introspect_token(self, token_string):
            data = {"token": token_string, "token_type_hint": "access_token"}
            auth = (client.client_id, client.client_secret)
            resp = iam_server.test_client.post(
                "/oauth/introspect", data=data, auth=auth
            )
            return resp.json

    require_oauth = ResourceProtector()
    require_oauth.register_token_validator(MyIntrospectTokenValidator())

    @app.route("/resource")
    @require_oauth("profile")
    def login():
        return {"success": True}

    return app


@pytest.fixture
def test_client(app):
    app.config["TESTING"] = True
    return app.test_client()


def test_valid_token_auth(iam_server, test_client, client, user):
    token = iam_server.random_token(client=client, subject=user)
    res = test_client.get(
        "/resource", headers={"Authorization": f"Bearer {token.access_token}"}
    )
    assert res.status_code == 200
    assert res.json["success"]


def test_invalid_token_auth(iam_server, test_client):
    res = test_client.get("/resource", headers={"Authorization": "Bearer invalid"})
    assert res.status_code == 401
