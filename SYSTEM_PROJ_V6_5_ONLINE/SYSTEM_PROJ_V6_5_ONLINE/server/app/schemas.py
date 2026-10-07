from __future__ import annotations
from typing import Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=3, max_length=180)
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    badge: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=200)

class MigratedAccountClaimIn(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    activation_code: str = Field(min_length=8, max_length=200)
    full_name: str = Field(min_length=3, max_length=180)
    email: EmailStr
    badge: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=200)

class LoginIn(BaseModel):
    login: str
    password: str
    device_name: str = ""

class RefreshIn(BaseModel):
    refresh_token: str

class ResetRequestIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=200)

class FlowUpdateIn(BaseModel):
    version: int
    transfer_requested: bool | None = None
    collection_forecast: str | None = None
    consumables_collected: bool
    container_status: str
    transport_stage: str

class ResponsibilityRequestIn(BaseModel):
    to_user_id: int
    reason: str = Field(min_length=3, max_length=2000)

class ResponsibilityDecisionIn(BaseModel):
    accept: bool

class AdminResponsibilityOverrideIn(BaseModel):
    to_user_id: int
    reason: str = Field(min_length=3, max_length=2000)

class RomaneioItemIn(BaseModel):
    category: str
    description: str = Field(min_length=2)
    quantity: float = 1
    unit: str = "UN"
    source_document: str | None = None
    observation: str | None = None

class UserApproveIn(BaseModel):
    role: str = "OPERATOR"

class MaterialIn(BaseModel):
    code: str
    description: str
    center: str = ""
    deposit: str = ""
    unit: str = "UN"
    active: bool = True

class ProjectCreateIn(BaseModel):
    os: str
    client: str
    title: str

class Page(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)
