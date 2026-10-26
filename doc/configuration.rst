Configuration
#############

pytest-iam can be configured by redefining or expanding the :meth:`~pytest_iam.iam_configuration` fixture.
This returns a :class:`dict` containing the canaille :doc:`canaille:references/configuration`.

.. code-block:: python

    @pytest.fixture(scope="session")
    def iam_configuration(iam_configuration):
        iam_configuration["CANAILLE_OIDC"]["REQUIRE_NONCE"] = False
        return iam_configuration

The configuration is also read from environment variables named after a Canaille setting, prefixed by ``PYTEST_IAM_``.

.. code-block:: bash

    env PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE=false pytest

The same variables can be written in a ``.pytest-iam.env`` file in the current directory.
The ``PYTEST_IAM_`` prefix is also required in this file.
Environment variables take precedence over the ``.pytest-iam.env`` file.

.. code-block:: bash
   :caption: .pytest-iam.env

    PYTEST_IAM_CANAILLE_OIDC__REQUIRE_NONCE=false
