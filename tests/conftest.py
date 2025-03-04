from typing import Generator, Any

import pytest
import os
from dotenv import load_dotenv

from sangsangstudio.clock import Clock, SystemClock
from sangsangstudio.repositories import (
    MySQLConnector,
    MySQLRepository)
from sangsangstudio.services import (
    PasswordHasher,
    UserService,
    CreateUserRequest,
    UserDto,
    LoginRequest)


load_dotenv()


@pytest.fixture
def mysql_host():
    return os.getenv("MYSQL_HOST")


@pytest.fixture
def mysql_password():
    return os.getenv("MYSQL_PASSWORD")


@pytest.fixture
def mysql_port():
    return int(os.getenv("MYSQL_PORT", default=3306))


@pytest.fixture
def mysql_user():
    return os.getenv("MYSQL_USER")


@pytest.fixture
def mysql_database():
    return os.getenv("MYSQL_DATABASE")


@pytest.fixture
def mysql_connector(mysql_user, mysql_host, mysql_password, mysql_port, mysql_database):
    connector = MySQLConnector(
        user=mysql_user,
        database=mysql_database,
        host=mysql_host,
        port=mysql_port,
        password=mysql_password)
    return connector


@pytest.fixture
def repository(mysql_connector, clock) -> Generator[MySQLRepository, Any, None]:
    repository = MySQLRepository(mysql_connector, clock)
    repository.create_tables()
    yield repository
    repository.drop_tables()


@pytest.fixture
def clock() -> Clock:
    return SystemClock()


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> bytes:
        return password.encode()

    def check(self, password: str, hashed: bytes) -> bool:
        return password.encode() == hashed.strip(b"\x00")


@pytest.fixture
def password_hasher() -> PasswordHasher:
    return FakePasswordHasher()


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


@pytest.fixture
def login_request(a_user, user_password):
    return LoginRequest(username=a_user.username, password=user_password)


@pytest.fixture
def a_session(user_service, login_request):
    return user_service.login(login_request)
