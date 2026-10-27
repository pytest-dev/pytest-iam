from pathlib import Path

pytest_plugins = ["pytester"]


def test_redefine_iam_configuration(pytester):
    conftest = Path(__file__).parent / "configuration_conftest.py"
    pytester.makeconftest(conftest.read_text())
    pytester.makepyfile(
        """
        def test_require_nonce(iam_server):
            assert iam_server.app.config["CANAILLE_OIDC"]["REQUIRE_NONCE"] is False
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=1)
