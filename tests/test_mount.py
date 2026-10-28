import httpx2
import pytest

pytest_plugins = ["pytester"]


def hello(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello"]


def test_mount(iam_server):
    """The IAM server sends its requests to the mounted application."""
    iam_server.mount("http://client.test", hello)

    res = iam_server.app.extensions["canaille_http"].client.get(
        "http://client.test/hello"
    )

    assert res.text == "Hello"


def test_unmount(iam_server):
    """The IAM server stops sending its requests to an unmounted application."""
    iam_server.mount("http://client.test", hello)
    iam_server.unmount("http://client.test")

    with pytest.raises(httpx2.ConnectError):
        iam_server.app.extensions["canaille_http"].client.get(
            "http://client.test/hello"
        )


def test_mount_does_not_leak_to_next_test(pytester):
    """An application mounted during a test is unmounted after the test."""
    pytester.makepyfile(
        """
        def hello(environ, start_response):
            start_response("200 OK", [])
            return [b"Hello"]

        def test_mount(iam_server):
            iam_server.mount("http://client.test", hello)

        def test_unmounted(iam_server):
            assert iam_server.mounts == {}
            assert iam_server.app.extensions["canaille_http"].mounts == {}
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=2)


def test_mount_in_module_fixture_is_kept(pytester):
    """An application mounted by a module fixture stays mounted for the module."""
    pytester.makepyfile(
        """
        import pytest

        def hello(environ, start_response):
            start_response("200 OK", [])
            return [b"Hello"]

        @pytest.fixture(scope="module", autouse=True)
        def mounted(iam_server):
            iam_server.mount("http://client.test", hello)

        def test_first(iam_server):
            iam_server.unmount("http://client.test")

        def test_second(iam_server):
            assert iam_server.mounts == {"http://client.test": hello}
        """
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=2)
