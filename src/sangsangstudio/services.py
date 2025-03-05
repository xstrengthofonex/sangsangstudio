import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import bcrypt

from sangsangstudio.clock import Clock
from sangsangstudio.entities import User, Session, Post, Content
from sangsangstudio.repositories import Repository


@dataclass(frozen=True)
class UserDto:
    id: int
    username: str


@dataclass(frozen=True)
class SessionDto:
    id: str
    created_on: datetime
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
    def __init__(self, repository: Repository, password_hasher: PasswordHasher, clock: Clock):
        self.repository = repository
        self.password_hasher = password_hasher
        self.clock = clock

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
        session = self.repository.find_session_by_user_id(user.id) if user else None
        if session:
            return self.session_to_dto(session)
        if user and self.password_hasher.check(request.password, user.password_hash):
            session = Session(
                id=self.generate_session_id(),
                created_on=self.clock.now(),
                user=user)
            self.repository.save_session(session)
            return self.session_to_dto(session)
        raise UnauthorizedLogin

    def find_session(self, session_id: str) -> SessionDto:
        session = self.repository.find_session_by_id(session_id)
        if not session:
            raise SessionNotFound()
        return self.session_to_dto(session)

    def logout(self, session_id: str):
        self.repository.delete_session(session_id)

    @staticmethod
    def user_to_dto(user: User) -> UserDto:
        return UserDto(
            id=user.id,
            username=user.username)

    def session_to_dto(self, session: Session) -> SessionDto:
        return SessionDto(
            id=session.id,
            created_on=session.created_on,
            user=self.user_to_dto(session.user))

    @staticmethod
    def generate_session_id() -> str:
        return str(uuid.uuid4().hex)


@dataclass(frozen=True)
class CreatePostRequest:
    session_id: str
    title: str


class PostStatusDto(Enum):
    DRAFT = 0
    PUBLISHED = 1


class ContentTypeDto(Enum):
    PARAGRAPH = 0


@dataclass(frozen=True)
class ContentDto:
    id: int
    type: ContentTypeDto
    text: str


@dataclass(frozen=True)
class PostDto:
    id: int
    author: UserDto
    created_on: datetime
    status: PostStatusDto
    title: str
    contents: list[ContentDto]


@dataclass(frozen=True)
class AddParagraphRequest:
    session_id: str
    post_id: int
    text: str


class PostNotFound(RuntimeError):
    pass


class PostService:
    def __init__(self, repository: Repository, clock: Clock):
        self.clock = clock
        self.repository = repository

    def create_post(self, request: CreatePostRequest) -> PostDto:
        session = self.repository.find_session_by_id(request.session_id)
        post = Post(author=session.user, created_on=self.clock.now(), title=request.title)
        self.repository.save_post(post)
        return self.post_to_dto(post)

    def find_post_by_id(self, post_id: int) -> PostDto:
        post = self.repository.find_post_by_id(post_id)
        return self.post_to_dto(post)

    def add_paragraph_to_post(self, request: AddParagraphRequest) -> PostDto:
        post = self.repository.find_post_by_id(request.post_id)
        if not post:
            raise PostNotFound()
        post.add_paragraph(request.text)
        self.repository.update_post(post)
        return self.post_to_dto(post)

    def post_to_dto(self, post: Post) -> PostDto:
        return PostDto(
            id=post.id,
            title=post.title,
            created_on=post.created_on,
            author=UserService.user_to_dto(post.author),
            status=PostStatusDto(post.status.value),
            contents=self.contents_to_dto(post.contents))

    @staticmethod
    def contents_to_dto(contents: list[Content]) -> list[ContentDto]:
        return [ContentDto(
            id=c.id, type=ContentTypeDto(c.type.value), text=c.text)
            for c in contents]
