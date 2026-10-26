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
