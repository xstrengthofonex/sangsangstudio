from abc import ABC, abstractmethod
from dataclasses import dataclass

import bcrypt

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
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def check(self, password: str, hashed: bytes) -> bool:
        return bcrypt.checkpw(password.encode(), hashed)


class UserService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.password_hasher = BcryptPasswordHasher()

    def create_user(self, request: CreateUserRequest) -> UserDto:
        password_hash = self.password_hasher.hash(request.password)
        user = User(username=request.username, password_hash=password_hash)
        self.repository.save_user(user)
        return self.user_to_dto(user)

    def find_user(self, user_id: int) -> UserDto:
        user = self.repository.find_user_by_id(user_id)
        return self.user_to_dto(user)

    def login(self, request: LoginRequest) -> UserDto:
        user = self.repository.find_user_by_username(request.username)
        if user and self.password_hasher.check(request.password, user.password_hash):
            return self.user_to_dto(user)
        raise UnauthorizedLogin

    @staticmethod
    def user_to_dto(user: User) -> UserDto:
        return UserDto(id=user.id, username=user.username)


