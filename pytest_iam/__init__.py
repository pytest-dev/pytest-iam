import datetime
import threading
import uuid
import wsgiref.simple_server

import portpicker
import pytest
from canaille import create_app
from canaille.app import models
from canaille.core.populate import fake_groups
from canaille.core.populate import fake_users
from canaille.oidc.installation import generate_keypair
from flask import g


class Server:
    port: int

    def __init__(self, app, port):
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
    def url(self):
        return f"http://localhost:{self.port}/"

    @property
    def random_user(self):
        return fake_users()[0]

    @property
    def random_group(self):
        return fake_groups(nb_users_max=0)[0]

    def login(self, user):
        self.logged_user = user

    def consent(self, user, client=None):
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
