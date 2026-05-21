from __future__ import annotations

from contextvars import ContextVar
import re
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 64
_SAFE_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
_request_id_var: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def generate_request_id() -> str:
    return f"req_{uuid4().hex}"


def sanitize_request_id(raw_request_id: str | None) -> str | None:
    if raw_request_id is None:
        return None
    candidate = raw_request_id.strip()
    if not candidate or len(candidate) > MAX_REQUEST_ID_LENGTH:
        return None
    if not _SAFE_REQUEST_ID_RE.fullmatch(candidate):
        return None
    return candidate


def get_request_id() -> str | None:
    return _request_id_var.get()


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id = sanitize_request_id(
            request_headers.get(REQUEST_ID_HEADER.lower())
        ) or generate_request_id()
        scope.setdefault("state", {})["request_id"] = request_id
        token = _request_id_var.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (
                        REQUEST_ID_HEADER.lower().encode("latin-1"),
                        request_id.encode("latin-1"),
                    )
                )
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _request_id_var.reset(token)
