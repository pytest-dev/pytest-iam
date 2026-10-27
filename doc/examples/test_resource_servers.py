import pytest
import requests
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc7662 import IntrospectTokenValidator
from flask import Flask


@pytest.fixture
def app(iam_server, client):
    class IAMTokenValidator(IntrospectTokenValidator):
        def introspect_token(self, token_string):
            response = requests.post(
                f"{iam_server.url}oauth/introspect",
                data={"token": token_string, "token_type_hint": "access_token"},
                auth=(client.client_id, client.client_secret),
            )
            return response.json()

    require_oauth = ResourceProtector()
    require_oauth.register_token_validator(IAMTokenValidator())

    app = Flask(__name__)

    @app.route("/resource")
    @require_oauth("profile")
    def resource():
        return {"success": True}

    return app


@pytest.fixture
def test_client(app):
    return app.test_client()


@pytest.fixture
def user_token(iam_server, client, user):
    token = iam_server.random_token(subject=user, client=client)
    yield token
    iam_server.backend.delete(token)


@pytest.fixture
def client_token(iam_server, client):
    token = iam_server.random_token(subject=None, client=client)
    yield token
    iam_server.backend.delete(token)


def test_user_token(test_client, user_token):
    res = test_client.get(
        "/resource", headers={"Authorization": f"Bearer {user_token.access_token}"}
    )
    assert res.status_code == 200


def test_client_token(test_client, client_token):
    res = test_client.get(
        "/resource", headers={"Authorization": f"Bearer {client_token.access_token}"}
    )
    assert res.status_code == 200


def test_invalid_token(test_client):
    res = test_client.get("/resource", headers={"Authorization": "Bearer invalid"})
    assert res.status_code == 401


def test_missing_scope(iam_server, client, user, test_client):
    token = iam_server.random_token(subject=user, client=client, scope=["openid"])
    res = test_client.get(
        "/resource", headers={"Authorization": f"Bearer {token.access_token}"}
    )
    assert res.status_code == 403
    iam_server.backend.delete(token)
