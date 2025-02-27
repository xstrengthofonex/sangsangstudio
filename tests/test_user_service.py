from dataclasses import dataclass

import pytest

from sangsangstudio.entities import User
from sangsangstudio.repositories import Repository


@dataclass(frozen=True)
class CreateUserRequest:
    username: str


@dataclass(frozen=True)
class UserDto:
    id: int
    username: str


class UserService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def create_user(self, request: CreateUserRequest) -> UserDto:
        user = User(username=request.username)
        self.repository.save_user(user)
        return UserDto(id=user.id, username=user.username)

    def find_user(self, user_id: int) -> UserDto:
        user = self.repository.find_user(user_id)
        return UserDto(id=user.id, username=user.username)


@pytest.fixture
def user_service(repository):
    return UserService(repository)


@pytest.fixture
def a_user(user_service) -> UserDto:
    request = CreateUserRequest(username="a_user")
    return user_service.create_user(request)


def test_user(user_service, a_user):
    assert user_service.find_user(a_user.id) == a_user

