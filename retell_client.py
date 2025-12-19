"""Retell SDK wrapper with basic retry semantics."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from retell import Retell
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential


class RetellClient:
    """Wrapper around the Retell SDK with sensible retries."""

    def __init__(self, api_key: str, base_url: Optional[str] = None) -> None:
        self.client = Retell(api_key=api_key, base_url=base_url) if base_url else Retell(api_key=api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def list_voices(self) -> List[Dict[str, Any]]:
        return self.client.voice.list()  # type: ignore[no-any-return]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def create_agent(self, **kwargs: Any) -> Dict[str, Any]:
        return self.client.agent.create(**kwargs)  # type: ignore[no-any-return]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def create_phone_number(self, **kwargs: Any) -> Dict[str, Any]:
        return self.client.phone_number.create(**kwargs)  # type: ignore[no-any-return]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def import_phone_number(self, **kwargs: Any) -> Dict[str, Any]:
        return self.client.phone_number.import_number(**kwargs)  # type: ignore[no-any-return]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def bind_phone_number(self, **kwargs: Any) -> Dict[str, Any]:
        return self.client.phone_number.bind(**kwargs)  # type: ignore[no-any-return]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def launch_batch_calls(self, **kwargs: Any) -> Dict[str, Any]:
        return self.client.batch_call.launch(**kwargs)  # type: ignore[no-any-return]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def get_transcript(self, **kwargs: Any) -> Dict[str, Any]:
        return self.client.transcript.get(**kwargs)  # type: ignore[no-any-return]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
    def export_transcript(self, **kwargs: Any) -> Dict[str, Any]:
        return self.client.transcript.export(**kwargs)  # type: ignore[no-any-return]

    @staticmethod
    def unwrap_retry_error(error: RetryError) -> Exception:
        """Return the original exception from a tenacity RetryError."""

        if error.last_attempt and error.last_attempt.failed:
            assert error.last_attempt.exception()
            return error.last_attempt.exception()
        return error
