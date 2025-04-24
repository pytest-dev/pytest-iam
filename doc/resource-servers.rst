Resource servers
================

If you are writing a resource server, you will probably want to test if your application can successfully check if a token is valid, to determine whether resources can be accessed.
If the access token is a `RFC9068 <https://www.rfc-editor.org/rfc/rfc9068.html>`_ JWT, then your application will need to check
the signature against the identity server JWKs. If the access token is not a JWT then your application will need to perform a
request against the identity server token introspection endpoint.

.. code:: python

    def test_valid_token_auth(iam_server, test_client, client, user):
        token = iam_server.random_token(client=client, subject=user)
        res = test_client.get(
            "/protected-resource", headers={"Authorization": f"Bearer {token.access_token}"}
        )
        assert res.status_code == 200


    def test_invalid_token_auth(iam_server, test_client):
        res = test_client.get(
            "/protected-resource", headers={"Authorization": "Bearer invalid"}
        )
        assert res.status_code == 401
