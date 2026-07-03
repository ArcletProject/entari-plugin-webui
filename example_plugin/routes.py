from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

_HERE = Path(__file__).parent
_STATIC_DIR = _HERE / "static"


class _EchoBody(BaseModel):
    message: str


class router:
    @staticmethod
    async def hello(request: Request) -> dict:
        name = request.query_params.get("name", "World")
        return {"success": True, "message": f"Hello, {name}!"}

    @staticmethod
    async def echo(body: _EchoBody) -> dict:
        return {"success": True, "echo": body.message}


async def serve_example_page() -> Response:
    html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return Response(html, media_type="text/html")
