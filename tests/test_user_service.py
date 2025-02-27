import pytest

from sangsangstudio.services import (
    CreateUserRequest, UserDto, UserService)


@pytest.fixture
def user_service(repository):
    return UserService(repository)


@pytest.fixture
def a_user(user_service) -> UserDto:
    request = CreateUserRequest(
        username="a_user",
        password="&tb&2l(@WqE&u")
    return user_service.create_user(request)


def test_user(user_service, a_user):
    assert user_service.find_user(a_user.id) == a_user

