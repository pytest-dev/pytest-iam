import datetime
import os
import threading
import uuid
import wsgiref.simple_server
from types import ModuleType
from typing import Any
from wsgiref.simple_server import WSGIRequestHandler

import portpicker
import pytest
from canaille import create_app
from canaille.app import models
from canaille.app.session import UserSession
from canaille.backends import Backend
from canaille.core.models import Group
from canaille.core.models import User
from canaille.core.populate import fake_groups
from canaille.core.populate import fake_users
from canaille.oidc.basemodels import Token
from flask import Flask
from flask import g
from joserfc.jwk import JWKRegistry
from werkzeug.test import Client


class Server:
    """A proxy object that is returned by the pytest fixture."""

    port: int
    """The port on which the local http server listens."""

    app: Flask
    """The authorization server flask app."""

    test_client: Client
    """A test client to interact with the IAM without performing real network requests."""

    models: ModuleType
    """The module containing the available model classes."""

    backend: Backend
    """The backend used to manage models."""

    logging: bool = False
    """Whether the request access log is enabled."""

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
        def login():
            if self.logged_user:
                now = datetime.datetime.now(datetime.timezone.utc)
                g.session = UserSession(user=self.logged_user, last_login_datetime=now)

        @self.app.after_request
        def logout(response):
            if self.logged_user:
                g.session = None

            return response

    def _make_request_handler(self):
        server = self

        class RequestHandler(WSGIRequestHandler):
            def log_request(self, code="-", size="-"):
                if server.logging:
                    super().log_request(code, size)

        return RequestHandler

    @property
    def url(self) -> str:
        """The URL at which the IAM server is accessible."""
        return f"http://localhost:{self.port}/"

    def random_user(self, **kwargs) -> User:
        """Generate a :class:`~canaille.core.models.User` with random values.

        Any parameter will be used instead of a random value.
        """
        with self.app.app_context():
            user = fake_users()[0]
            user.update(**kwargs)
            user.save()

        return user

    def random_group(self, **kwargs) -> Group:
        """Generate a :class:`~canaille.core.models.Group` with random values.

        Any parameter will be used instead of a random value.
        """
        with self.app.app_context():
            group = fake_groups(nb_users_max=0)[0]
            group.update(**kwargs)
            group.save()

        return group

    def random_token(self, subject: User, client: Client, **kwargs) -> Token:
        """Generate a test :class:`~canaille.oidc.basemodels.Token` with random values.

        Any parameter will be used instead of a random value.
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
                issue_date=datetime.datetime.now(datetime.timezone.utc),
                lifetime=3600,
                audience=[client],
            )
            self.backend.update(token, **kwargs)
            self.backend.save(token)

        return token

    def login(self, user: User):
        """Open a session for the user in the IAM session.

        This allows to skip the connection screen.
        """
        self.logged_user = user

    def logout(self):
        """Close the current user session if existing."""
        self.logged_user = None

    def consent(self, user: User, client: Client | None = None):
        """Make a user consent to share data with OIDC clients.

        :param client: If :const:`None`, all existing clients are consented.
        """
        with self.app.app_context():
            clients = [client] if client else self.backend.query(models.Client)

            consents = [
                self.models.Consent(
                    consent_id=str(uuid.uuid4()),
                    client=client,
                    subject=user,
                    scope=client.scope,
                    issue_date=datetime.datetime.now(datetime.timezone.utc),
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
def iam_server_port():
    return portpicker.pick_unused_port()


@pytest.fixture(scope="session")
def iam_configuration(tmp_path_factory, iam_server_port) -> dict[str, Any]:
    """Fixture for editing the configuration of :meth:`~pytest_iam.iam_server`."""
    os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"

    jwk = JWKRegistry.generate_key("RSA", 1024)
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
                "root": {"level": "DEBUG", "handlers": ["canaille"]},
            },
        },
        "CANAILLE_OIDC": {
            "DYNAMIC_CLIENT_REGISTRATION_OPEN": True,
            "ACTIVE_JWKS": [jwk.as_dict()],
        },
    }


@pytest.fixture(scope="session")
def iam_server(iam_configuration, iam_server_port) -> Server:
    """Fixture that creates a Canaille server listening a random port in a thread."""
    app = create_app(
        config=iam_configuration, env_file=".pytest-iam.env", env_prefix="PYTEST_IAM_"
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
