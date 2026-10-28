import pytest


@pytest.fixture
def user(iam_server):
    user = iam_server.models.User(
        user_name="user",
        emails=["email@example.org"],
        password="correct horse battery staple",
    )
    iam_server.backend.save(user)
    yield user
    iam_server.backend.delete(user)


@pytest.fixture
def group(iam_server, user):
    group = iam_server.models.Group(
        display_name="group",
        members=[user],
    )
    iam_server.backend.save(group)
    yield group
    iam_server.backend.delete(group)


@pytest.fixture
def client(iam_server):
    client = iam_server.models.Client(
        client_id="client_id",
        client_secret="client_secret",
        client_name="My Application",
        client_uri="http://client.test",
        redirect_uris=["http://client.test/authorize"],
        post_logout_redirect_uris=["http://client.test/logged-out"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="client_secret_basic",
        scope=["openid", "profile", "groups"],
    )
    iam_server.backend.save(client)
    yield client
    iam_server.backend.delete(client)
