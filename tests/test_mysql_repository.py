import pytest

from sangsangstudio.entities import User


@pytest.fixture
def a_user(repository):
    user = User(id=1, username="user")
    repository.save_user(user)
    return user


def test_create_user(a_user, repository):
    assert repository.find_user(a_user.id) == a_user


def test_update_user(a_user, repository):
    new_username = "new_username"
    a_user.username = new_username
    repository.update_user(a_user)
    found_user = repository.find_user(a_user.id)
    assert found_user.username == new_username


def test_delete_user(a_user, repository):
    repository.delete_user(a_user.id)
    assert repository.find_user(a_user.id) is None
