Configuration
#############

pytest-iam can be configured by redefining or expanding the :meth:`~pytest_iam.iam_configuration` fixture.
This returns a :const:`dict` containing the canaille :doc:`canaille:configuration`.

.. code-block:: python

    @pytest.fixture(scope="session")
    def iam_configuration(iam_configuration):
        iam_configuration["CANAILLE"]["ACL"]["DEFAULT"]["WRITE"].append("groups")
        return iam_configuration

The configuration will also be read from a `.pytest-iam.env` file if existing.

.. code-block:: bash
   :caption: .pytest-iam.env

    CANAILLE_OIDC__REQUIRE_NONCE=false

It can also be read from any environment var with a valid Canaille setting name prefixed by `PYTEST_IAM_`.

.. code-block:: bash

    env PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE=false pytest
