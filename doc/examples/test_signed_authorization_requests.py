import json
from urllib.parse import parse_qs
from urllib.parse import urlsplit

import pytest
from joserfc import jwt
from joserfc.jwk import KeySet
from joserfc.jwk import RSAKey


@pytest.fixture(scope="session")
def client_key():
    return RSAKey.generate_key(2048, auto_kid=True)


@pytest.fixture
def client(iam_server, client_key):
    client = iam_server.models.Client(
        client_id="client_id",
        client_secret="client_secret",
        client_name="My Application",
        client_uri="http://client.test",
        redirect_uris=["http://client.test/authorize"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="client_secret_basic",
        scope=["openid", "profile"],
        jwks=json.dumps(KeySet([client_key]).as_dict(private=False)),
        require_signed_request_object=True,
    )
    iam_server.backend.save(client)
    yield client
    iam_server.backend.delete(client)


def test_signed_request_object(iam_server, client, client_key, user):
    iam_server.login(user)
    iam_server.consent(user, client)

    claims = {
        "iss": client.client_id,
        "aud": iam_server.url.rstrip("/"),
        "client_id": client.client_id,
        "response_type": "code",
        "redirect_uri": "http://client.test/authorize",
        "scope": "openid profile",
        "state": "state",
        "nonce": "nonce",
    }
    request_object = jwt.encode(
        {"alg": "RS256", "kid": client_key.kid}, claims, client_key
    )

    res = iam_server.test_client.get(
        "/oauth/authorize",
        query_string={"client_id": client.client_id, "request": request_object},
    )

    assert res.status_code == 302
    assert "code" in parse_qs(urlsplit(res.location).query)


def test_unsigned_request_is_rejected(iam_server, client, user):
    iam_server.login(user)
    iam_server.consent(user, client)

    res = iam_server.test_client.get(
        "/oauth/authorize",
        query_string={
            "client_id": client.client_id,
            "response_type": "code",
            "redirect_uri": "http://client.test/authorize",
            "scope": "openid profile",
            "nonce": "nonce",
        },
    )

    assert res.status_code == 400


def test_request_object_signed_with_another_key(iam_server, client, user):
    iam_server.login(user)
    iam_server.consent(user, client)

    other_key = RSAKey.generate_key(2048, auto_kid=True)
    claims = {
        "client_id": client.client_id,
        "response_type": "code",
        "redirect_uri": "http://client.test/authorize",
        "scope": "openid profile",
        "nonce": "nonce",
    }
    request_object = jwt.encode(
        {"alg": "RS256", "kid": other_key.kid}, claims, other_key
    )

    res = iam_server.test_client.get(
        "/oauth/authorize",
        query_string={"client_id": client.client_id, "request": request_object},
    )

    assert res.status_code == 400


@pytest.fixture
def user(iam_server):
    user = iam_server.random_user()
    yield user
    iam_server.backend.delete(user)
