Configuration
#############

pytest-iam can be configured by redefining or expanding the :meth:`~pytest_iam.iam_configuration` fixture.
This returns a :const:`dict` containing the canaille :doc:`canaille:configuration`.

   .. code:: python

    @pytest.fixture(scope="session")
    def iam_configuration(iam_configuration):
        iam_configuration["ACL"]["DEFAULT"]["WRITE"].append("groups")
        return iam_configuration
