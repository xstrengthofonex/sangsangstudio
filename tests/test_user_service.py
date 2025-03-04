import pytest

from sangsangstudio.services import (
    CreateUserRequest,
    UserDto,
    UserService,
    UnauthorizedLogin,
    LoginRequest,
    PasswordHasher, SystemClock, Clock)


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> bytes:
        return password.encode()

    def check(self, password: str, hashed: bytes) -> bool:
        return password.encode() == hashed.strip(b"\x00")


@pytest.fixture
def password_hasher() -> PasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def clock() -> Clock:
    return SystemClock()


@pytest.fixture
def user_service(repository, password_hasher, clock):
    return UserService(repository, password_hasher, clock)


@pytest.fixture
def user_password():
    return "&tb&2l(@WqE&u"


@pytest.fixture
def create_user_request(user_password) -> CreateUserRequest:
    return CreateUserRequest(
        username="a_user",
        password=user_password)


@pytest.fixture
def a_user(user_service, create_user_request) -> UserDto:
    return user_service.create_user(create_user_request)


def test_create_user(user_service, a_user):
    assert user_service.find_user(a_user.id) == a_user

@pytest.fixture
def login_request(a_user, user_password):
    return LoginRequest(username=a_user.username, password=user_password)


@pytest.fixture
def a_session(user_service, login_request):
    return user_service.login(login_request)


def test_login_fail(user_service, a_user):
    with pytest.raises(UnauthorizedLogin):
        request = LoginRequest(username=a_user.username, password="wrongpassword")
        user_service.login(request)


def test_login_success(user_service, a_session):
    assert a_session == user_service.find_session(a_session.id)


def test_multiple_logins_returns_session(user_service, a_session, login_request):
    another_session = user_service.login(login_request)
    assert another_session == a_session
