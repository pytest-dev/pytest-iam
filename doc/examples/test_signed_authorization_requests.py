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
def jwks_uri_client(iam_server, client_key):
    jwks = json.dumps(KeySet([client_key]).as_dict(private=False)).encode()

    def client_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "application/json")])
        return [jwks]

    iam_server.mount("http://client.test", client_app)

    client = iam_server.models.Client(
        client_id="jwks_uri_client_id",
        client_secret="client_secret",
        client_name="My Application",
        client_uri="http://client.test",
        redirect_uris=["http://client.test/authorize"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="client_secret_basic",
        scope=["openid", "profile"],
        jwks_uri="http://client.test/jwks.json",
        require_signed_request_object=True,
    )
    iam_server.backend.save(client)
    yield client
    iam_server.backend.delete(client)


def test_request_object_with_jwks_uri(iam_server, jwks_uri_client, client_key, user):
    iam_server.login(user)
    iam_server.consent(user, jwks_uri_client)

    claims = {
        "iss": jwks_uri_client.client_id,
        "aud": iam_server.url.rstrip("/"),
        "client_id": jwks_uri_client.client_id,
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
        query_string={
            "client_id": jwks_uri_client.client_id,
            "request": request_object,
        },
    )

    assert res.status_code == 302
    assert "code" in parse_qs(urlsplit(res.location).query)


def test_request_object_by_reference(iam_server, client, client_key, user):
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

    def client_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "application/oauth-authz-req+jwt")])
        return [request_object.encode()]

    iam_server.mount("http://client.test", client_app)
    iam_server.backend.update(client, request_uris=["http://client.test/request.jwt"])
    iam_server.backend.save(client)

    res = iam_server.test_client.get(
        "/oauth/authorize",
        query_string={
            "client_id": client.client_id,
            "request_uri": "http://client.test/request.jwt",
        },
    )

    assert res.status_code == 302
    assert "code" in parse_qs(urlsplit(res.location).query)


def test_unregistered_request_uri_is_rejected(iam_server, client, user):
    iam_server.login(user)
    iam_server.consent(user, client)

    res = iam_server.test_client.get(
        "/oauth/authorize",
        query_string={
            "client_id": client.client_id,
            "request_uri": "http://client.test/request.jwt",
        },
    )

    assert res.status_code == 400
