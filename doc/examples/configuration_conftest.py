import pytest


@pytest.fixture(scope="session")
def iam_configuration(iam_configuration):
    iam_configuration["CANAILLE_OIDC"]["REQUIRE_NONCE"] = False
    return iam_configuration
