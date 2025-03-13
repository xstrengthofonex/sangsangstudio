from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass
class Entity:
    id: int | None = None


@dataclass
class User(Entity):
    username: str = ""
    password_hash: bytes = b""


@dataclass
class Session(Entity):
    key: str = ""
    user: User | None = None
    created_on: datetime = field(default_factory=datetime.now)


class PostStatus(Enum):
    DRAFT = 0
    PUBLISHED = 1


class ContentType(Enum):
    PARAGRAPH = 0
    IMAGE = 1


@dataclass
class Content(Entity):
    post_id: int | None = None
    type: ContentType = ContentType.PARAGRAPH
    sequence: int = 1
    text: str = ""
    src: str = ""


@dataclass
class Post(Entity):
    author: User | None = None
    created_on: datetime = field(default_factory=datetime.now)
    title: str = ""
    status: PostStatus = PostStatus.DRAFT
    contents: list[Content] = field(default_factory=list)

    def add_paragraph(self, text: str):
        self.contents.append(
            Content(type=ContentType.PARAGRAPH, sequence=self.get_next_order(), text=text))

    def add_image(self, src: str, text: str):
        self.contents.append(
            Content(type=ContentType.IMAGE, sequence=self.get_next_order(), text=text, src=src))

    def get_next_order(self) -> int:
        if not self.contents:
            return 1
        return max(c.sequence for c in self.contents) + 1


@dataclass
class Admin(Entity):
    user: User | None = None
    first_name: str = ""
    family_name: str = ""
