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


class Server:
    port: int

    def __init__(self, app, port):
        self.app = app
        self.port = port
        self.httpd = wsgiref.simple_server.make_server("localhost", port, app)
        self.models = models

    @property
    def url(self):
        return f"http://localhost:{self.port}/"

    @property
    def random_user(self):
        return fake_users()[0]

    @property
    def random_group(self):
        return fake_groups(nb_users_max=0)[0]


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
