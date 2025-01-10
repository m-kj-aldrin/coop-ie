from typing import Generic, TypeVar
from pydantic import BaseModel, field_validator, Field
from packages.crm.types import SubjectType
from packages.utils.html_parser import IncidentHtmlDescriptionParser
from dataclasses import asdict, dataclass
from typing import Any
from typing import Optional
from datetime import datetime
from app.logger import logger

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
        # logger.debug(f"Parsing HTML description: {value}")
        if value is None:
            return None
        return IncidentHtmlDescriptionParser.parse_text(value)


class CreationFailureIncident(BaseModel):
    ticketnumber: str
    incidentid: str
    description: str

    @field_validator("description", mode="after")
    @classmethod
    def parse_html_description(cls, value: str | None) -> str | None:
        """Parse HTML description using IncidentHtmlDescriptionParser."""
        # logger.debug(f"Parsing HTML description: {value}")
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


@dataclass
class IncidentData:
    description: Optional[str] = None
    coop_resolvedon: Optional[datetime] = None
    coop_closecasenotification: Optional[bool] = None
    coop_resolution: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[SubjectType] = None


# from dataclasses import dataclass


@dataclass
class creation_failure:
    """Data model for customer incidents.

    Attributes:
        Orsak: The reason for the incident
        Personnummer: Customer's personal identification number
        Ansökningsdatum: Date of application
        Kanal: Channel used for the application
        Butiksnummer: Store number where the incident occurred
        Kvittonummer: Receipt number for the transaction
        Ordernummer: Order number related to the incident
        Cas: Case number for the incident
        Epost: Customer's email address
    """

    Orsak: str
    Personnummer: str
    Ansökningsdatum: str
    Kanal: str
    Butiksnummer: str
    Kvittonummer: str
    Ordernummer: str
    CAS: str
    Epost: str
