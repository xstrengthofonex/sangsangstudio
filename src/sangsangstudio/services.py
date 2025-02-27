from abc import ABC, abstractmethod
from dataclasses import dataclass

from sangsangstudio.entities import User
from sangsangstudio.repositories import Repository


@dataclass(frozen=True)
class CreateUserRequest:
    username: str
    password: str


@dataclass(frozen=True)
class UserDto:
    id: int
    username: str


class UnauthorizedLogin(RuntimeError):
    pass


@dataclass(frozen=True)
class LoginRequest:
    username: str
    password: str


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> bytes:
        pass

    @abstractmethod
    def check(self, password: str, hashed: bytes) -> bool:
        pass


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, password: str) -> bytes:
        pass

    def check(self, password: str, hashed: bytes) -> bool:
        pass


class UserService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.password_hasher = BcryptPasswordHasher()

    def create_user(self, request: CreateUserRequest) -> UserDto:
        user = User(username=request.username)
        self.repository.save_user(user)
        return UserDto(id=user.id, username=user.username)

    def find_user(self, user_id: int) -> UserDto:
        user = self.repository.find_user(user_id)
        return UserDto(id=user.id, username=user.username)

    def login(self, request):
        raise UnauthorizedLogin


