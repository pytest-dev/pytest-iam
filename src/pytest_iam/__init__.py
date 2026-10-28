import datetime
import os
import threading
import uuid
import wsgiref.simple_server
from collections.abc import Iterator
from types import ModuleType
from typing import Any
from wsgiref.simple_server import WSGIRequestHandler
from wsgiref.simple_server import WSGIServer

import portpicker
import pytest
from blinker import signal
from canaille import create_app
from canaille.app import models
from canaille.app.session import UserSession
from canaille.backends import Backend
from canaille.core.models import Group
from canaille.core.models import User
from canaille.core.populate import fake_groups
from canaille.core.populate import fake_users
from canaille.oidc.basemodels import Client
from canaille.oidc.basemodels import Consent
from canaille.oidc.basemodels import Token
from flask import Flask
from flask import Response
from flask import g
from flask import request
from flask import request_started
from joserfc.jwk import JWKRegistry
from werkzeug.test import Client as TestClient


class Server:
    """The IAM server, returned by the :func:`~pytest_iam.iam_server` fixture."""

    port: int
    """The port of the HTTP server."""

    app: Flask
    """The Flask application of the IAM server."""

    test_client: TestClient
    """A test client that sends requests to the IAM server without network."""

    models: ModuleType
    """The module of the Canaille models, such as ``models.User``."""

    backend: Backend
    """The Canaille backend, to save, get and delete models."""

    logging: bool = False
    """Whether the HTTP server prints one line per request."""

    httpd: WSGIServer
    """The HTTP server."""

    logged_user: User | None
    """The user logged in with :meth:`login`, or :data:`None`."""

    def __init__(self, app: Flask, port: int, backend: Backend, logging: bool = False):
        self.app = app
        self.test_client = app.test_client()
        self.backend = backend
        self.port = port
        self.logging = logging
        self.httpd = wsgiref.simple_server.make_server(
            "localhost", port, app, handler_class=self._make_request_handler()
        )
        self.models = models
        self.logged_user = None

        @self.app.before_request
        def login() -> None:
            if self.logged_user:
                now = datetime.datetime.now(datetime.UTC)
                g.session = UserSession(user=self.logged_user, last_login_datetime=now)

        @self.app.after_request
        def logout(response: Response) -> Response:
            if self.logged_user:
                g.session = None

            return response

        # The application context stays active during the tests,
        # so requests from the test client share the same g.
        @request_started.connect_via(self.app, weak=False)
        def save_globals(sender: Flask, **extra: Any) -> None:
            request.environ["pytest_iam.globals"] = set(g)

        @self.app.teardown_request
        def restore_globals(exc: BaseException | None) -> None:
            for name in set(g) - request.environ.get("pytest_iam.globals", set()):
                g.pop(name)

        @signal("user_logged_out").connect_via(self.app, weak=False)
        def forget_logged_user(sender: Flask, user: User, **extra: Any) -> None:
            if self.logged_user and self.logged_user.id == user.id:
                self.logged_user = None

    def _make_request_handler(self) -> type[WSGIRequestHandler]:
        server = self

        class RequestHandler(WSGIRequestHandler):
            def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
                if server.logging:
                    super().log_request(code, size)

        return RequestHandler

    @property
    def url(self) -> str:
        """The URL of the IAM server, ending with a slash."""
        return f"http://localhost:{self.port}/"

    def random_user(self, **kwargs: Any) -> User:
        """Create and save a :class:`~canaille.core.models.User` with random values.

        Keyword arguments set some of the values.
        """
        with self.app.app_context():
            user = fake_users()[0]
            self.backend.update(user, **kwargs)
            self.backend.save(user)

        return user

    def random_group(self, **kwargs: Any) -> Group:
        """Create and save a :class:`~canaille.core.models.Group` with random values.

        Keyword arguments set some of the values.
        """
        with self.app.app_context():
            groups = fake_groups(nb_users_max=0)
            group = groups[0]
            self.backend.update(group, **kwargs)
            self.backend.save(group)

        return group

    def random_token(
        self, subject: User | None, client: Client, **kwargs: Any
    ) -> Token:
        """Create and save an access :class:`~canaille.oidc.basemodels.Token` for a client.

        With a :data:`None` subject, the token belongs to the client only.
        The token has the scopes of the client, and lasts 3600 seconds.
        Keyword arguments set some of the values.
        """
        with self.app.app_context():
            token = self.models.Token(
                id=str(uuid.uuid4()),
                token_id=str(uuid.uuid4()),
                access_token=str(uuid.uuid4()),
                client=client,
                subject=subject,
                type="access_token",
                refresh_token=str(uuid.uuid4()),
                scope=client.scope,
                issue_date=datetime.datetime.now(datetime.UTC),
                lifetime=3600,
                audience=[client],
            )
            self.backend.update(token, **kwargs)
            self.backend.save(token)

        return token

    def login(self, user: User) -> None:
        """Log a user in on the IAM server, without the login form.

        The user is logged out at the end of the test,
        or when the user logs out on the IAM server.
        A login made by a module or session scoped fixture lasts until :meth:`logout`.
        """
        self.logged_user = user

    def logout(self) -> None:
        """Log out the user logged in with :meth:`login`."""
        self.logged_user = None

    def consent(
        self, user: User, client: Client | None = None
    ) -> Consent | list[Consent] | None:
        """Record the consent of a user for a client.

        With a :data:`None` client, the user consents to all the existing clients.
        Return the consent, the list of consents when several clients exist,
        or :data:`None` when no client exists.
        """
        with self.app.app_context():
            clients = [client] if client else self.backend.query(models.Client)

            consents = [
                self.models.Consent(
                    consent_id=str(uuid.uuid4()),
                    client=client,
                    subject=user,
                    scope=client.scope,
                    issue_date=datetime.datetime.now(datetime.UTC),
                )
                for client in clients
            ]

            for consent in consents:
                self.backend.save(consent)

        if len(consents) > 1:
            return consents
        if len(consents) == 1:
            return consents[0]
        return None


@pytest.fixture(scope="session")
def iam_server_port() -> int:
    """Session fixture that returns the port of the IAM server.

    By default, it is a free port. Redefine it to use a fixed port.
    """
    return portpicker.pick_unused_port()


@pytest.fixture(scope="session")
def iam_configuration(iam_server_port: int) -> dict[str, Any]:
    """Session fixture that returns the settings of the IAM server.

    Redefine it to change the settings, as described in :doc:`configuration`.
    """
    os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"

    jwk = JWKRegistry.generate_key("RSA", 2048)
    jwk.ensure_kid()

    return {
        "TESTING": True,
        "ENV_FILE": None,
        "SECRET_KEY": str(uuid.uuid4()),
        "WTF_CSRF_ENABLED": False,
        "PREFERRED_URL_SCHEME": "http",
        "SERVER_NAME": f"localhost:{iam_server_port}",
        "CANAILLE": {
            "DATABASE": "memory",
            "ENABLE_REGISTRATION": True,
            "JAVASCRIPT": False,
            "ACL": {
                "DEFAULT": {
                    "PERMISSIONS": ["use_oidc", "manage_oidc"],
                }
            },
            "LOGGING": {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                    }
                },
                "handlers": {
                    "canaille": {
                        "class": "logging.NullHandler",
                        "formatter": "default",
                    }
                },
                "loggers": {
                    "canaille": {"level": "DEBUG", "handlers": ["canaille"]},
                },
            },
        },
        "CANAILLE_OIDC": {
            "DYNAMIC_CLIENT_REGISTRATION_OPEN": True,
            "ACTIVE_JWKS": [jwk.as_dict(private=True)],
        },
    }


@pytest.fixture(scope="session")
def iam_server(
    iam_configuration: dict[str, Any], iam_server_port: int
) -> Iterator[Server]:
    """Session fixture that starts the IAM server in a thread, and returns a :class:`Server`."""
    app = create_app(
        config=iam_configuration,
        env_file=".pytest-iam.env",
        env_prefix="PYTEST_IAM_",
        config_file=False,
    )
    server = Server(app, iam_server_port, Backend.instance)

    server_thread = threading.Thread(target=server.httpd.serve_forever)
    server_thread.start()
    try:
        with app.app_context():
            yield server
    finally:
        server.httpd.shutdown()
        server_thread.join()


@pytest.fixture(autouse=True)
def iam_restore_login(request: pytest.FixtureRequest) -> Iterator[None]:
    """Autouse fixture that logs out the users logged in during each test.

    It undoes the :meth:`~pytest_iam.Server.login` calls,
    and the logins through the forms of :attr:`~pytest_iam.Server.test_client`.
    """
    if "iam_server" not in request.fixturenames:
        yield
        return

    server = request.getfixturevalue("iam_server")
    logged_user = server.logged_user
    # Werkzeug has no public API to list the cookies of a test client.
    cookies = server.test_client._cookies
    saved_cookies = dict(cookies) if cookies is not None else {}
    yield
    server.logged_user = logged_user
    if cookies is not None:
        cookies.clear()
        cookies.update(saved_cookies)
