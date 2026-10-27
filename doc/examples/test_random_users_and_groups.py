import pytest


@pytest.fixture
def user(iam_server):
    user = iam_server.random_user()
    yield user
    iam_server.backend.delete(user)


@pytest.fixture
def group(iam_server, user):
    group = iam_server.random_group()
    group.members = group.members + [user]
    iam_server.backend.save(group)
    yield group
    iam_server.backend.delete(group)


def test_group_members(iam_server, user, group):
    group = iam_server.backend.get(iam_server.models.Group, id=group.id)
    assert user in group.members
