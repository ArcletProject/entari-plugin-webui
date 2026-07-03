from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    message: str | None = None
    code: str = "error"
    status: int = 400

    def __post_init__(self) -> None:
        if self.message is None:
            self.message = self.code.replace("_", " ").capitalize()
        self.args = (self.message,)


@dataclass
class PluginNotFound(AppError):
    code: str = "plugin_not_found"
    status: int = 404


@dataclass
class ConfigSectionNotFound(AppError):
    code: str = "section_not_found"
    status: int = 404


@dataclass
class MarketError(AppError):
    code: str = "market_error"
    status: int = 400


@dataclass
class UnknownPlugin(MarketError):
    code: str = "unknown_plugin"
    status: int = 400


@dataclass
class AuthRequired(AppError):
    code: str = "auth_required"
    status: int = 401


@dataclass
class Forbidden(AppError):
    code: str = "forbidden"
    status: int = 403


@dataclass
class TooManyRequests(AppError):
    code: str = "rate_limited"
    status: int = 429
    retry_after: int | None = None
