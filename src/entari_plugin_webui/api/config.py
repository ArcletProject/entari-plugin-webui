from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..services.config_service import (
    ConfigSectionNotFound,
    get_schema_for_section,
    get_section,
    list_sections,
    update_section,
)
from .deps import require_auth

router = APIRouter(prefix="/api/config", tags=["config"], dependencies=[Depends(require_auth)])


class SectionBody(BaseModel):
    data: dict | list


@router.get("/{section}/schema")
async def schema(section: str):
    try:
        return {"success": True, "section": section, **get_schema_for_section(section)}
    except ConfigSectionNotFound:
        return {"success": False, "code": "section_not_found"}, 404


@router.get("")
async def list_():
    return {"success": True, **list_sections()}


@router.get("/{section}")
async def get_(section: str):
    try:
        return {"success": True, "section": section, "data": get_section(section)}
    except KeyError:
        return {"success": False, "code": "section_not_found"}, 404


@router.put("/{section}")
async def put_(section: str, body: SectionBody):
    try:
        update_section(section, body.data)
        return {"success": True, "message": "已保存"}
    except ConfigSectionNotFound:
        return {"success": False, "code": "section_not_found"}, 404
