def test_server_configuration(iam_server):
    res = iam_server.test_client.get("/.well-known/openid-configuration")
    assert res.json["issuer"] in iam_server.url


def test_logs(iam_server, caplog):
    response = iam_server.test_client.post(
        "/oauth/register",
        json={
            "client_name": "Nubla Dashboard",
            "client_uri": "http://client.test",
            "redirect_uris": ["http://client.test/authorize"],
            "grant_types": ["authorization_code"],
            "response_types": ["code", "token", "id_token"],
            "token_endpoint_auth_method": "client_secret_basic",
            "scope": "openid profile groups",
        },
    )

    assert caplog.records[0].msg == "client registration endpoint request: POST: %s"

    client_id = response.json["client_id"]
    client = iam_server.backend.get(iam_server.models.Client, client_id=client_id)
    iam_server.backend.delete(client)


def test_random_user(iam_server):
    assert isinstance(iam_server.random_user(), iam_server.models.User)


def test_random_group(iam_server):
    assert isinstance(iam_server.random_group(), iam_server.models.Group)
