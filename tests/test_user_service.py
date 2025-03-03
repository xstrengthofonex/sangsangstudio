import pytest

from sangsangstudio.services import (
    CreateUserRequest, UserDto, UserService, UnauthorizedLogin, LoginRequest)


@pytest.fixture
def user_service(repository):
    return UserService(repository)


@pytest.fixture
def user_password():
    return "&tb&2l(@WqE&u"


@pytest.fixture
def a_user(user_service, user_password) -> UserDto:
    request = CreateUserRequest(
        username="a_user",
        password=user_password)
    return user_service.create_user(request)


def test_create_user(user_service, a_user):
    assert user_service.find_user(a_user.id) == a_user


def test_login_fail(user_service, a_user):
    with pytest.raises(UnauthorizedLogin):
        request = LoginRequest(username=a_user.username, password="wrongpassword")
        user_service.login(request)


def test_login_success(user_service, a_user, user_password):
    request = LoginRequest(username=a_user.username, password=user_password)
    logged_in_user = user_service.login(request)
    assert logged_in_user == a_user
