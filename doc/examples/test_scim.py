import pytest
from scim2_client.engines.wsgi import WSGISCIMClient
from scim2_models import ForbiddenException


@pytest.fixture
def scim_client(iam_server):
    client = iam_server.models.Client(
        client_id="scim_client_id",
        client_secret="client_secret",
        client_name="My Provisioning Application",
        client_uri="http://client.test",
        grant_types=["client_credentials"],
        token_endpoint_auth_method="client_secret_basic",
        scope=["scim:read", "scim:write"],
    )
    iam_server.backend.save(client)
    yield client
    iam_server.backend.delete(client)


@pytest.fixture
def scim(iam_server, scim_client):
    token = iam_server.random_token(subject=None, client=scim_client)
    scim = WSGISCIMClient(
        iam_server.app,
        base_url=f"{iam_server.url}scim/v2",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    scim.discover()
    return scim


def test_create_user(iam_server, scim):
    User = scim.get_resource_model("User")

    scim.create(
        User(
            user_name="bjensen",
            name={"formatted": "Barbara Jensen", "family_name": "Jensen"},
            emails=[{"value": "bjensen@example.org"}],
            active=True,
        )
    )

    user = iam_server.backend.get(iam_server.models.User, user_name="bjensen")
    assert user.emails == ["bjensen@example.org"]
    iam_server.backend.delete(user)


def test_token_without_scim_scope(iam_server, scim_client):
    token = iam_server.random_token(subject=None, client=scim_client, scope=["openid"])
    scim = WSGISCIMClient(
        iam_server.app,
        base_url=f"{iam_server.url}scim/v2",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    scim.discover()

    with pytest.raises(ForbiddenException):
        scim.query(scim.get_resource_model("User"))
