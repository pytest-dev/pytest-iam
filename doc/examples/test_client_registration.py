import pytest


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


def test_client_is_registered(iam_server, client):
    assert iam_server.backend.get(iam_server.models.Client, client_id="client_id")


def test_dynamic_registration(iam_server):
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

    client = iam_server.backend.get(iam_server.models.Client, client_id=client_id)
    assert client.client_secret == client_secret
    iam_server.backend.delete(client)
