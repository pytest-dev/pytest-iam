import uuid

import pytest
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask import redirect
from flask import session
from flask import url_for


@pytest.fixture
def app(iam_server, client):
    app = Flask(__name__)
    app.config["SERVER_NAME"] = "client.test"
    app.config["SECRET_KEY"] = str(uuid.uuid4())

    oauth = OAuth(app)
    oauth.register(
        name="iam",
        client_id=client.client_id,
        client_secret=client.client_secret,
        server_metadata_url=f"{iam_server.url}.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile"},
    )

    @app.route("/protected")
    def protected():
        if "user" not in session:
            return oauth.iam.authorize_redirect(url_for("authorize", _external=True))
        return f"Hello, {session['user']['sub']}!"

    @app.route("/create")
    def create():
        return oauth.iam.authorize_redirect(
            url_for("authorize", _external=True), prompt="create"
        )

    @app.route("/authorize")
    def authorize():
        token = oauth.iam.authorize_access_token()
        session["user"] = token["userinfo"]
        return redirect(url_for("protected"))

    return app


@pytest.fixture
def test_client(app):
    return app.test_client()


def test_login(iam_server, client, user, test_client):
    # 1. the protected page redirects to the IAM server
    res = test_client.get("/protected")

    # 2. the IAM server redirects to its login form
    res = iam_server.test_client.get(res.location)

    # 3. fill the login form
    res = iam_server.test_client.post(res.location, data={"login": "user"})

    # 4. fill the password form
    res = iam_server.test_client.post(
        res.location, data={"password": "correct horse battery staple"}
    )

    # 5. fill the consent form, the IAM server redirects to the application with a code
    res = iam_server.test_client.post(res.location, data={"answer": "accept"})

    # 6. the application exchanges the code for a token
    res = test_client.get(res.location)

    # 7. the protected page is now accessible
    res = test_client.get(res.location)
    assert res.text == "Hello, user!"


def test_login_shortcuts(iam_server, client, user, test_client):
    iam_server.login(user)
    iam_server.consent(user, client)

    # 1. the protected page redirects to the IAM server
    res = test_client.get("/protected")

    # 2. the IAM server redirects to the application with a code
    res = iam_server.test_client.get(res.location)

    # 3. the application exchanges the code for a token
    res = test_client.get(res.location)

    # 4. the protected page is now accessible
    res = test_client.get(res.location)
    assert res.text == "Hello, user!"


def test_account_creation(iam_server, client, test_client):
    # 1. the creation page redirects to the IAM server, with prompt=create
    res = test_client.get("/create")

    # 2. the IAM server redirects to its registration form
    res = iam_server.test_client.get(res.location)
    res = iam_server.test_client.get(res.location)

    # 3. fill the registration form
    res = iam_server.test_client.post(
        res.location,
        data={
            "user_name": "new_user",
            "given_name": "John",
            "family_name": "Doe",
            "emails-0": "john@example.org",
            "password1": "correct horse battery staple",
            "password2": "correct horse battery staple",
        },
    )

    # 4. fill the consent form, the IAM server redirects to the application with a code
    res = iam_server.test_client.post(res.location, data={"answer": "accept"})

    # 5. the application exchanges the code for a token
    res = test_client.get(res.location)

    # 6. the protected page is now accessible
    res = test_client.get(res.location)
    assert res.text == "Hello, new_user!"

    user = iam_server.backend.get(iam_server.models.User, user_name="new_user")
    iam_server.backend.delete(user)
