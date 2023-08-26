import pytest


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
        formatted_name="John Doe",
        emails=["email@example.org"],
        password="password",
    )
    inst.save()
    yield inst
    inst.delete()
