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
