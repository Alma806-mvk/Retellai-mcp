"""FastMCP server wrapping Retell SDK operations."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastmcp import FastMCP
from fastmcp.responses import ErrorResponse
from pydantic import ValidationError
from tenacity import RetryError

from config import load_settings
from retell_client import RetellClient
from schemas import (
    BatchCallLaunchRequest,
    BatchCallLaunchResponse,
    HungarianAgentRequest,
    HungarianAgentResponse,
    PhoneNumberBindRequest,
    PhoneNumberCreateRequest,
    PhoneNumberImportRequest,
    PhoneNumberResponse,
    TranscriptExportRequest,
    TranscriptExportResponse,
    TranscriptRequest,
    TranscriptResponse,
    Voice,
    VoiceListResponse,
)
from storage import AgentRecord, Storage

settings = load_settings()
client = RetellClient(api_key=settings.retell_api_key, base_url=settings.retell_base_url)
storage = Storage(settings.database_path)

mcp = FastMCP(
    name="retell-mcp-server",
    version="0.1.0",
    description="MCP server providing access to Retell voice automation APIs",
    stateless_http=True,
    streamable_http=True,
)


@mcp.tool()
def list_voices() -> VoiceListResponse:
    """List voices configured in Retell."""

    try:
        voices = client.list_voices()
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    parsed: List[Voice] = []
    for item in voices:
        parsed.append(
            Voice(
                voice_id=item.get("voice_id") or item.get("id"),
                name=item.get("name"),
                locale=item.get("locale"),
            )
        )
    return VoiceListResponse(voices=parsed)


@mcp.tool()
def create_hungarian_salon_agent(request: HungarianAgentRequest) -> HungarianAgentResponse:
    """Create a Hungarian-speaking salon agent and persist metadata locally."""

    try:
        payload = request.dict()
    except ValidationError as exc:  # pragma: no cover - handled by FastMCP
        raise exc

    try:
        response = client.create_agent(**payload)
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    agent_id = response.get("agent_id") or response.get("id")
    created_at = datetime.utcnow()
    record = AgentRecord(
        agent_id=agent_id,
        name=request.name,
        voice_id=request.voice_id,
        prompt=request.prompt,
        phone_number=request.phone_number,
        created_at=created_at,
    )
    storage.save_agent(record)

    if request.phone_number:
        try:
            client.bind_phone_number(agent_id=agent_id, phone_number=request.phone_number)
        except RetryError as exc:
            raise RetellClient.unwrap_retry_error(exc)

    return HungarianAgentResponse(
        agent_id=agent_id,
        name=request.name,
        voice_id=request.voice_id,
        phone_number=request.phone_number,
        created_at=created_at,
    )


@mcp.tool()
def create_phone_number(request: PhoneNumberCreateRequest) -> PhoneNumberResponse:
    """Provision a new phone number with Retell."""

    try:
        response = client.create_phone_number(**request.dict(exclude_none=True))
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    return PhoneNumberResponse(
        phone_number=response.get("phone_number") or response.get("number"),
        provider_id=response.get("id"),
        friendly_name=response.get("friendly_name"),
    )


@mcp.tool()
def import_phone_number(request: PhoneNumberImportRequest) -> PhoneNumberResponse:
    """Import an existing phone number into Retell."""

    try:
        response = client.import_phone_number(**request.dict(exclude_none=True))
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    return PhoneNumberResponse(
        phone_number=response.get("phone_number") or response.get("number"),
        provider_id=response.get("id"),
        friendly_name=response.get("friendly_name"),
    )


@mcp.tool()
def bind_phone_number(request: PhoneNumberBindRequest) -> PhoneNumberResponse:
    """Bind an imported/provisioned phone number to an agent."""

    try:
        response = client.bind_phone_number(**request.dict())
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    return PhoneNumberResponse(
        phone_number=response.get("phone_number") or request.phone_number,
        provider_id=response.get("id"),
        friendly_name=response.get("friendly_name"),
    )


@mcp.tool()
def launch_batch_calls(request: BatchCallLaunchRequest) -> BatchCallLaunchResponse:
    """Kick off a batch of outbound calls for a given agent."""

    try:
        response = client.launch_batch_calls(**request.dict(exclude_none=True))
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    batch_id = response.get("batch_id") or response.get("id")
    return BatchCallLaunchResponse(
        batch_id=batch_id,
        agent_id=request.agent_id,
        targets=request.targets,
        submitted_at=datetime.utcnow(),
    )


@mcp.tool()
def get_transcript(request: TranscriptRequest) -> TranscriptResponse:
    """Retrieve a call transcript and store it locally."""

    try:
        response = client.get_transcript(**request.dict())
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    transcript_text = response.get("transcript") or response.get("text") or ""
    record = storage.upsert_transcript(call_id=request.call_id, transcript=transcript_text)
    return TranscriptResponse(
        call_id=request.call_id,
        transcript=record.transcript,
        collected_at=record.collected_at,
    )


@mcp.tool()
def export_transcript(request: TranscriptExportRequest) -> TranscriptExportResponse:
    """Export a transcript to an external destination."""

    record = storage.get_transcript(request.call_id)
    if not record:
        return ErrorResponse(message=f"Transcript for call {request.call_id} not found")

    try:
        client.export_transcript(call_id=request.call_id, destination=str(request.destination))
    except RetryError as exc:
        raise RetellClient.unwrap_retry_error(exc)

    return TranscriptExportResponse(
        call_id=request.call_id,
        destination=request.destination,
        status="submitted",
        exported_at=datetime.utcnow(),
    )


if __name__ == "__main__":
    mcp.run()
