"""Pydantic schemas for request and response payloads."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class Voice(BaseModel):
    voice_id: str = Field(..., description="Voice identifier")
    name: Optional[str] = Field(None, description="Human readable name")
    locale: Optional[str] = Field(None, description="Locale for the voice")


class VoiceListResponse(BaseModel):
    voices: List[Voice]


class HungarianAgentRequest(BaseModel):
    name: str = Field(..., description="Agent name")
    voice_id: str = Field(..., description="Voice to associate with the agent")
    prompt: str = Field(..., description="Prompt in Hungarian for the salon agent")
    phone_number: Optional[str] = Field(None, description="Existing phone number to bind")

    @validator("prompt")
    def prompt_must_be_hungarian(cls, value: str) -> str:
        if len(value.split()) < 12:
            raise ValueError("Prompt must include at least 12 words for sufficient context")
        if "szalon" not in value.lower():
            raise ValueError("Prompt must reference 'szalon' to ensure salon context in Hungarian")
        return value


class HungarianAgentResponse(BaseModel):
    agent_id: str
    name: str
    voice_id: str
    phone_number: Optional[str]
    created_at: datetime


class PhoneNumberCreateRequest(BaseModel):
    country: str = Field(..., description="Country code, e.g. HU")
    area_code: Optional[str] = Field(None, description="Optional area code for the number")
    friendly_name: Optional[str] = Field(None, description="Friendly label for the phone number")


class PhoneNumberImportRequest(BaseModel):
    phone_number: str = Field(..., description="E.164 formatted phone number to import")
    carrier: Optional[str] = Field(None, description="Carrier notes for auditing")


class PhoneNumberResponse(BaseModel):
    phone_number: str
    provider_id: Optional[str] = None
    friendly_name: Optional[str] = None


class PhoneNumberBindRequest(BaseModel):
    agent_id: str
    phone_number: str


class BatchCallLaunchRequest(BaseModel):
    agent_id: str
    targets: List[str] = Field(..., description="List of E.164 phone numbers to call")
    metadata: Optional[dict[str, Any]] = None

    @validator("targets")
    def at_least_one_target(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("At least one target phone number is required")
        return value


class BatchCallLaunchResponse(BaseModel):
    batch_id: str
    agent_id: str
    targets: List[str]
    submitted_at: datetime


class TranscriptRequest(BaseModel):
    call_id: str


class TranscriptResponse(BaseModel):
    call_id: str
    transcript: str
    collected_at: datetime


class TranscriptExportRequest(BaseModel):
    call_id: str
    destination: HttpUrl


class TranscriptExportResponse(BaseModel):
    call_id: str
    destination: HttpUrl
    status: str
    exported_at: datetime
