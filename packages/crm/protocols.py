from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class User:
    username: str
    password: str


@dataclass
class Cookie:
    name: str
    value: str
    expires: float | None = None
    domain: str | None = None
    path: str | None = "/"

    def to_json(self):
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, object]) -> "Cookie":
        return cls(**data)


class AuthenticateProtocol(Protocol):

    def __init__(self, login_url: str): ...

    @property
    def cookies(self) -> dict[str, Cookie]: ...

    @property
    def is_authenticated(self) -> bool: ...

    def login(self, user: User | None = None) -> "AuthenticateProtocol": ...

    def logout(self) -> "AuthenticateProtocol": ...

    def cookies_as_tuples(self) -> list[tuple[str, str]]: ...
