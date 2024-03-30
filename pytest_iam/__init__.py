import datetime
import threading
import uuid
import wsgiref.simple_server
from types import ModuleType
from typing import Any
from typing import Dict

import portpicker
import pytest
from canaille import create_app
from canaille.app import models
from canaille.core.models import Group
from canaille.core.models import User
from canaille.core.populate import fake_groups
from canaille.core.populate import fake_users
from canaille.oidc.basemodels import Token
from canaille.oidc.installation import generate_keypair
from flask import Flask
from flask import g


class Server:
    """A proxy object that is returned by the pytest fixture."""

    #: The port on which the local http server listens
    port: int

    #: The authorization server flask app
    app: Flask

    #: The module containing the available model classes
    models: ModuleType

    def __init__(self, app, port: int):
        self.app = app
        self.port = port
        self.httpd = wsgiref.simple_server.make_server("localhost", port, app)
        self.models = models
        self.logged_user = None

        @self.app.before_request
        def logged_user():
            if self.logged_user:
                g.user = self.logged_user

    @property
    def url(self) -> str:
        """The URL at which the IAM server is accessible."""
        return f"http://localhost:{self.port}/"

    def random_user(self, **kwargs) -> User:
        """Generates a :class:`~canaille.core.models.User` with random values.

        Any parameter will be used instead of a random value.
        """
        with self.app.app_context():
            user = fake_users()[0]
            user.update(**kwargs)
            user.save()

        return user

    def random_group(self, **kwargs) -> Group:
        """Generates a :class:`~canaille.core.models.Group` with random values.

        Any parameter will be used instead of a random value.
        """
        with self.app.app_context():
            group = fake_groups(nb_users_max=0)[0]
            group.update(**kwargs)
            group.save()

        return group

    def random_token(self, subject, client, **kwargs) -> Token:
        """Generates a test :class:`~canaille.oidc.basemodels.Token` with
        random values.

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
            token.update(**kwargs)
            token.save()

        return token

    def login(self, user):
        """Opens a session for the user in the IAM session.

        This allows to skip the connection screen.
        """
        self.logged_user = user

    def consent(self, user, client=None):
        """Make a user consent to share data with OIDC clients.

        :param client: If :const:`None`, all existing clients are consented.
        """

        with self.app.app_context():
            clients = [client] if client else models.Client.query()

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
                consent.save()

        if len(consents) > 1:
            return consents
        if len(consents) == 1:
            return consents[0]
        return None


@pytest.fixture(scope="session")
def iam_configuration(tmp_path_factory) -> Dict[str, Any]:
    """Fixture for editing the configuration of
    :meth:`~pytest_iam.iam_server`."""

    private_key, public_key = generate_keypair()
    return {
        "TESTING": True,
        "SECRET_KEY": str(uuid.uuid4()),
        "WTF_CSRF_ENABLED": False,
        "CANAILLE": {
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
            "JWT": {
                "PUBLIC_KEY": public_key,
                "PRIVATE_KEY": private_key,
            },
        },
    }


@pytest.fixture(scope="session")
def iam_server(iam_configuration) -> Server:
    """Fixture that creates a Canaille server listening a random port in a
    thread."""

    port = portpicker.pick_unused_port()
    app = create_app(config=iam_configuration)
    server = Server(app, port)

    server_thread = threading.Thread(target=server.httpd.serve_forever)
    server_thread.start()
    try:
        with app.app_context():
            yield server
    finally:
        server.httpd.shutdown()
        server_thread.join()
