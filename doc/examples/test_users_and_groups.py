def test_group_members(iam_server, user, group):
    group = iam_server.backend.get(iam_server.models.Group, display_name="group")
    assert group.members == [user]
