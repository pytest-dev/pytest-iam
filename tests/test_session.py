from blinker import signal

pytest_plugins = ["pytester"]


def test_login_does_not_leak_to_next_test(pytester):
    """A user logged in during a test is logged out after the test."""
    pytester.makepyfile(
        """
        def test_login(iam_server):
            iam_server.login(iam_server.random_user())

        def test_logged_out(iam_server):
            assert iam_server.logged_user is None
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=2)


def test_login_in_module_fixture_is_kept(pytester):
    """A user logged in by a module-scoped fixture stays logged in for the module."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(scope="module")
        def user(iam_server):
            user = iam_server.random_user()
            iam_server.login(user)
            return user

        def test_first(iam_server, user):
            assert iam_server.logged_user == user

        def test_second(iam_server, user):
            assert iam_server.logged_user == user
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=2)


def test_logout_on_iam_server(iam_server):
    """A user logged in with login() is logged out by the IAM server logout page."""
    user = iam_server.random_user()
    iam_server.login(user)

    iam_server.test_client.get("/logout")

    assert iam_server.logged_user is None
    iam_server.backend.delete(user)


def test_logout_of_another_user_keeps_login(iam_server):
    """Logging out another user does not log out the user logged in with login()."""
    user = iam_server.random_user()
    other = iam_server.random_user()
    iam_server.login(user)

    with iam_server.app.test_request_context():
        signal("user_logged_out").send(iam_server.app, user=other)

    assert iam_server.logged_user == user
    iam_server.backend.delete(user)
    iam_server.backend.delete(other)


FORM_LOGIN = """
import pytest


@pytest.fixture(scope="module")
def client(iam_server):
    client = iam_server.models.Client(
        client_id="client_id",
        client_secret="client_secret",
        client_name="client",
        client_uri="http://client.test",
        redirect_uris=["http://client.test/authorize"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="client_secret_basic",
        scope=["openid"],
    )
    iam_server.backend.save(client)
    return client


@pytest.fixture(scope="module")
def user(iam_server):
    return iam_server.random_user(password="correct horse battery staple")


def authorize(iam_server, client):
    return iam_server.test_client.get(
        "/oauth/authorize",
        query_string={
            "client_id": client.client_id,
            "response_type": "code",
            "redirect_uri": "http://client.test/authorize",
            "scope": "openid",
            "nonce": "nonce",
        },
    )


def login_with_forms(iam_server, client, user):
    res = authorize(iam_server, client)
    res = iam_server.test_client.post(res.location, data={"login": user.user_name})
    iam_server.test_client.post(
        res.location, data={"password": "correct horse battery staple"}
    )
"""


def test_form_login_does_not_leak_to_next_test(pytester):
    """A user logged in with the login form is logged out after the test."""
    pytester.makepyfile(
        FORM_LOGIN
        + """
def test_login(iam_server, client, user):
    login_with_forms(iam_server, client, user)
    assert authorize(iam_server, client).status_code == 200

def test_logged_out(iam_server, client):
    res = authorize(iam_server, client)
    assert res.status_code == 302
    assert "/login" in res.location
"""
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=2)


def test_form_login_in_module_fixture_is_kept(pytester):
    """A user logged in with the login form by a module fixture stays logged in."""
    pytester.makepyfile(
        FORM_LOGIN
        + """
@pytest.fixture(scope="module")
def logged_in(iam_server, client, user):
    login_with_forms(iam_server, client, user)

def test_first(iam_server, client, logged_in):
    assert authorize(iam_server, client).status_code == 200

def test_second(iam_server, client, logged_in):
    assert authorize(iam_server, client).status_code == 200
"""
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=2)
