import pytest


@pytest.fixture
def user(iam_server):
    user = iam_server.models.User(
        user_name="user",
        emails=["email@example.org"],
        password="correct horse battery staple",
    )
    iam_server.backend.save(user)
    yield user
    iam_server.backend.delete(user)


@pytest.fixture
def group(iam_server, user):
    group = iam_server.models.Group(
        display_name="group",
        members=[user],
    )
    iam_server.backend.save(group)
    yield group
    iam_server.backend.delete(group)


def test_group_members(iam_server, user, group):
    group = iam_server.backend.get(iam_server.models.Group, display_name="group")
    assert group.members == [user]
