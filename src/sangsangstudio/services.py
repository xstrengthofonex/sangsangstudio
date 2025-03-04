import base64
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

import bcrypt

from sangsangstudio.entities import User, Session
from sangsangstudio.repositories import Repository


@dataclass(frozen=True)
class UserDto:
    id: int
    username: str


@dataclass(frozen=True)
class SessionDto:
    id: str
    user: UserDto


@dataclass(frozen=True)
class CreateUserRequest:
    username: str
    password: str


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


class SessionNotFound(RuntimeError):
    pass


class UserService:
    def __init__(self, repository: Repository, password_hasher: PasswordHasher):
        self.repository = repository
        self.password_hasher = password_hasher

    def create_user(self, request: CreateUserRequest) -> UserDto:
        password_hash = self.password_hasher.hash(request.password)
        user = User(username=request.username, password_hash=password_hash)
        self.repository.save_user(user)
        return self.user_to_dto(user)

    def find_user(self, user_id: int) -> UserDto:
        user = self.repository.find_user_by_id(user_id)
        return self.user_to_dto(user)

    def login(self, request: LoginRequest) -> SessionDto:
        user = self.repository.find_user_by_username(request.username)
        if user and self.password_hasher.check(request.password, user.password_hash):
            session = Session(id=self.generate_session_id(), user=user)
            self.repository.save_session(session)
            return self.session_to_dto(session)
        raise UnauthorizedLogin

    def find_session(self, session_id: str) -> SessionDto:
        session = self.repository.find_session_by_id(session_id)
        if not session:
            raise SessionNotFound()
        return self.session_to_dto(session)

    @staticmethod
    def user_to_dto(user: User) -> UserDto:
        return UserDto(id=user.id, username=user.username)

    def session_to_dto(self, session: Session) -> SessionDto:
        return SessionDto(id=session.id, user=self.user_to_dto(session.user))

    @staticmethod
    def generate_session_id() -> str:
        return str(uuid.uuid4()).strip("-")




