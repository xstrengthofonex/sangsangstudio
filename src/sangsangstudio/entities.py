from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass
class User:
    id: int | None = None
    username: str = ""
    password_hash: bytes = b""


@dataclass
class Session:
    id: str
    user: User
    created_on: datetime | None = field(default_factory=datetime.now)


class PostStatus(Enum):
    DRAFT = 0
    PUBLISHED = 1


@dataclass
class Post:
    id: int | None = None
    author: User | None = None
    created_on: datetime = field(default_factory=datetime.now)
    title: str = ""
    status: PostStatus = PostStatus.DRAFT
