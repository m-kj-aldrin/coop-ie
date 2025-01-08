from typing import Generic, TypeVar
from pydantic import BaseModel, field_validator, Field
from packages.utils.html_parser import IncidentHtmlDescriptionParser
from dataclasses import asdict, dataclass
from typing import Any

T = TypeVar("T")


class ODataResponse(BaseModel, Generic[T]):
    value: list[T]


class Contact(BaseModel):
    contactid: str
    mmid: str | None = Field(alias="coop_external_customer_id", default=None)
    fullname: str
    email: str | None = Field(alias="emailaddress1", default=None)


class Incident(BaseModel):
    title: str
    description: str | None = None
    contact: Contact | None = Field(alias="customerid_contact", default=None)

    @field_validator("description", mode="after")
    @classmethod
    def parse_html_description(cls, value: str | None) -> str | None:
        """Parse HTML description using IncidentHtmlDescriptionParser."""
        if value is None:
            return None
        return IncidentHtmlDescriptionParser.parse_text(value)


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
    def from_json(cls, data: dict[str, Any]) -> "Cookie":
        return cls(**data)
