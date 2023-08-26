import datetime
import threading
import uuid
import wsgiref.simple_server
from types import ModuleType

import portpicker
import pytest
from canaille import create_app
from canaille.app import models
from canaille.core.populate import fake_groups
from canaille.core.populate import fake_users
from canaille.oidc.installation import generate_keypair
from flask import Flask
from flask import g


class Server:
    """
    A proxy object that is returned by the pytest fixture.
    """

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
        """
        The URL at which the IAM server is accessible.
        """
        return f"http://localhost:{self.port}/"

    def random_user(self, **kwargs):
        """
        Generates a :class:`~canaille.core.models.User` with random values.
        Any parameter will be used instead of a random value.
        """
        user = fake_users()[0]
        user.update(**kwargs)
        user.save()
        return user

    def random_group(self, **kwargs):
        """
        Generates a :class:`~canaille.core.models.Group` with random values.
        Any parameter will be used instead of a random value.
        """
        group = fake_groups(nb_users_max=0)[0]
        group.update(**kwargs)
        group.save()
        return group

    def random_token(self, subject, client, **kwargs):
        """
        Generates a test :class:`~canaille.oidc.basemodels.Token` with random values.
        Any parameter will be used instead of a random value.
        """
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
        """
        Opens a session for the user in the IAM session.
        This allows to skip the connection screen.
        """
        self.logged_user = user

    def consent(self, user, client=None):
        """
        Make a user consent to share data with OIDC clients.

        :param client: If :const:`None`, all existing clients are consented.
        """
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
def iam_server():
    port = portpicker.pick_unused_port()
    private_key, public_key = generate_keypair()
    config = {
        "TESTING": True,
        "JAVASCRIPT": False,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": str(uuid.uuid4()),
        "OIDC": {
            "DYNAMIC_CLIENT_REGISTRATION_OPEN": True,
            "JWT": {
                "PUBLIC_KEY": public_key,
                "PRIVATE_KEY": private_key,
            },
        },
        "ACL": {
            "DEFAULT": {
                "PERMISSIONS": ["use_oidc", "manage_oidc"],
            }
        },
    }
    app = create_app(config=config)
    server = Server(app, port)

    server_thread = threading.Thread(target=server.httpd.serve_forever)
    server_thread.start()
    try:
        with app.app_context():
            yield server
    finally:
        server.httpd.shutdown()
        server_thread.join()
