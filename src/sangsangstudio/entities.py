from dataclasses import dataclass


@dataclass
class User:
    id: int | None = None
    username: str = ""
    password_hash: bytes = b""
