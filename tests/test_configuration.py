pytest_plugins = ["pytester"]


def test_env_file(pytester):
    """Prefixed variables in .pytest-iam.env are read."""
    pytester.path.joinpath(".pytest-iam.env").write_text(
        "PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE=false\n"
    )
    pytester.makepyfile(
        """
        def test_require_nonce(iam_server):
            assert iam_server.app.config["CANAILLE_OIDC"]["REQUIRE_NONCE"] is False
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)


def test_environment_variable_overrides_env_file(pytester, monkeypatch):
    """Environment variables take precedence over .pytest-iam.env."""
    pytester.path.joinpath(".pytest-iam.env").write_text(
        "PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE=false\n"
    )
    monkeypatch.setenv("PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE", "true")
    pytester.makepyfile(
        """
        def test_require_nonce(iam_server):
            assert iam_server.app.config["CANAILLE_OIDC"]["REQUIRE_NONCE"] is True
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)


def test_environment_variable_does_not_override_fixture(pytester, monkeypatch):
    """Environment variables do not change the values set by iam_configuration."""
    monkeypatch.setenv("PYTEST_IAM_CANAILLE__ENABLE_REGISTRATION", "false")
    pytester.makepyfile(
        """
        def test_enable_registration(iam_server):
            assert iam_server.app.config["CANAILLE"]["ENABLE_REGISTRATION"] is True
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)


def test_redefine_iam_server_port(pytester):
    """Redefining iam_server_port sets the port of the server."""
    pytester.makepyfile(
        """
        import portpicker
        import pytest

        PORT = portpicker.pick_unused_port()

        @pytest.fixture(scope="session")
        def iam_server_port():
            return PORT

        def test_port(iam_server):
            assert iam_server.url == f"http://localhost:{PORT}/"
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)
