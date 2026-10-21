from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from ..services.config_service import (
    get_etag,
    get_schema_for_section,
    get_section,
    list_sections,
    report_to_dict,
    update_section,
)
from .deps import require_auth

router = APIRouter(prefix="/api/config", tags=["config"], dependencies=[Depends(require_auth)])


class SectionBody(BaseModel):
    data: dict | list


@router.get("/{section}/schema")
async def schema(section: str):
    return {"success": True, "section": section, **get_schema_for_section(section)}


@router.get("")
async def list_():
    return {"success": True, **list_sections()}


@router.get("/{section}")
async def get_(section: str):
    return {"success": True, "section": section, "data": get_section(section), "etag": get_etag()}


@router.put("/{section}")
async def put_(section: str, body: SectionBody, if_match: str | None = Header(default=None, alias="If-Match")):
    report = await update_section(section, body.data, if_match=if_match)
    return {
        "success": report.ok,
        "message": "已保存" if report.ok else "部分配置未生效",
        "apply": report_to_dict(report),
        "data": get_section(section),
        "etag": get_etag(),
    }
