from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from backend.app.core.permissions import Role
from backend.app.core.security import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


class DocumentType(StrEnum):
    CC = "CC"
    CE = "CE"
    PASSPORT = "PASSPORT"
    NIT = "NIT"
    TI = "TI"


class PersonType(StrEnum):
    NATURAL = "natural"
    LEGAL = "legal"


def _lower(value: str) -> str:
    return value.strip().lower()


NormalizedEmail = Annotated[EmailStr, AfterValidator(_lower)]
Password = Annotated[str, Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
DocumentNumber = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9-]{3,20}$")]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9+()\s-]{7,20}$")]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterIn(_Strict):
    email: NormalizedEmail
    password: Password
    full_name: Name
    person_type: PersonType = PersonType.NATURAL
    document_type: DocumentType
    document_number: DocumentNumber
    phone: Phone | None = None
    country: ShortText | None = None
    city: ShortText | None = None
    accept_privacy_policy: bool = Field(
        description="Consentimiento de tratamiento de datos (Ley 1581 de 2012).",
    )


class UserCreateByStaff(_Strict):
    email: NormalizedEmail
    full_name: Name
    role: Role = Role.CLIENT
    person_type: PersonType = PersonType.NATURAL
    document_type: DocumentType | None = None
    document_number: DocumentNumber | None = None
    phone: Phone | None = None
    country: ShortText | None = None
    city: ShortText | None = None


class UserUpdateMe(_Strict):
    full_name: Name | None = None
    phone: Phone | None = None
    country: ShortText | None = None
    city: ShortText | None = None


class UserUpdateByStaff(UserUpdateMe):
    person_type: PersonType | None = None
    document_type: DocumentType | None = None
    document_number: DocumentNumber | None = None
    role: Role | None = None


class UserStatusIn(_Strict):
    is_active: bool


class ChangePasswordIn(_Strict):
    current_password: str = Field(max_length=MAX_PASSWORD_LENGTH)
    new_password: Password


class UserOut(BaseModel):
    id: str
    email: str
    email_verified: bool
    full_name: str
    person_type: PersonType | None = None
    document_type: DocumentType | None = None
    document_number: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    role: Role
    is_active: bool
    permissions: list[str] = []
    created_at: datetime


class UserPage(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    limit: int
