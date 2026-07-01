from __future__ import annotations

_PERMS: dict[str, dict[str, str]] = {}


class PermissionsRegistry:
    @staticmethod
    def add(key: str, label_key: str) -> None:
        _PERMS[key] = {"key": key, "label_key": label_key}

    @staticmethod
    def all() -> list[dict[str, str]]:
        return list(_PERMS.values())


def get_permissions() -> list[dict[str, str]]:
    return PermissionsRegistry.all()
