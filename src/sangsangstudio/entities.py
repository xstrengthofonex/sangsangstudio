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


class ContentType(Enum):
    PARAGRAPH = 0
    IMAGE = 1


@dataclass
class Content:
    id: int | None = None
    type: ContentType = ContentType.PARAGRAPH
    order: int = 1
    text: str = ""
    src: str = ""


@dataclass
class Post:
    id: int | None = None
    author: User | None = None
    created_on: datetime = field(default_factory=datetime.now)
    title: str = ""
    status: PostStatus = PostStatus.DRAFT
    contents: list[Content] = field(default_factory=list)

    def add_paragraph(self, text: str):
        self.contents.append(
            Content(type=ContentType.PARAGRAPH, order=self.get_next_order(), text=text))

    def add_image(self, src: str, text: str):
        self.contents.append(
            Content(type=ContentType.IMAGE, order=self.get_next_order(), text=text, src=src))

    def get_next_order(self) -> int:
        if not self.contents:
            return 1
        return max(c.order for c in self.contents) + 1
