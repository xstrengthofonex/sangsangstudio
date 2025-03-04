from dataclasses import dataclass, field
from datetime import datetime


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