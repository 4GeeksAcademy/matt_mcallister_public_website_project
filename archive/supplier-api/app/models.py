from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from .constants import COUNTRY_TO_CURRENCY, VALID_CATEGORIES, VALID_COUNTRIES


class SupplierStatus(str, Enum):
    active = "active"
    suspended = "suspended"


class SupplierBase(BaseModel):
    name: str = Field(min_length=1)
    country: str
    categories: list[str] = Field(min_length=1)
    rate_per_shipment: float = Field(gt=0)
    currency: str
    status: SupplierStatus
    service_zone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        if value not in VALID_COUNTRIES:
            raise ValueError(f"country must be one of {VALID_COUNTRIES}")
        return value

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, value: list[str]) -> list[str]:
        invalid = [category for category in value if category not in VALID_CATEGORIES]
        if invalid:
            raise ValueError(f"invalid categories: {invalid}")
        return value

    @model_validator(mode="after")
    def validate_currency_country_pair(self) -> "SupplierBase":
        expected_currency = COUNTRY_TO_CURRENCY[self.country]
        if self.currency != expected_currency:
            raise ValueError(
                f"currency must be {expected_currency} when country is {self.country}"
            )
        return self


class SupplierCreate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: int
    rate_updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RateUpdateRequest(BaseModel):
    rate_per_shipment: float = Field(gt=0)


class StatusUpdateRequest(BaseModel):
    status: SupplierStatus


class SupplierInDb(SupplierBase):
    rate_updated_at: datetime

    @field_validator("rate_updated_at", mode="before")
    @classmethod
    def ensure_datetime(cls, value: str | datetime) -> datetime:
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
