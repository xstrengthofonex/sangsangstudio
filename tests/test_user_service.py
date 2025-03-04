import pytest

from sangsangstudio.services import (
    CreateUserRequest,
    UserDto,
    UserService,
    UnauthorizedLogin,
    LoginRequest,
    PasswordHasher,
    BcryptPasswordHasher)


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> bytes:
        return password.encode()

    def check(self, password: str, hashed: bytes) -> bool:
        return password.encode() == hashed.strip(b"\x00")


@pytest.fixture
def password_hasher() -> PasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def user_service(repository, password_hasher):
    return UserService(repository, password_hasher)


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


def test_login_fail(user_service, create_user_request):
    user_service.password_hasher = BcryptPasswordHasher()
    a_user = user_service.create_user(create_user_request)
    with pytest.raises(UnauthorizedLogin):
        request = LoginRequest(username=a_user.username, password="wrongpassword")
        user_service.login(request)


def test_login_success(user_service, create_user_request):
    user_service.password_hasher = BcryptPasswordHasher()
    a_user = user_service.create_user(create_user_request)
    request = LoginRequest(username=a_user.username, password=create_user_request.password)
    session = user_service.login(request)
    assert session == user_service.find_session(session.id)
