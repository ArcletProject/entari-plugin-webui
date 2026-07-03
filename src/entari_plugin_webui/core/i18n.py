from __future__ import annotations

_I18N: dict[str, dict[str, str]] = {}


class I18nRegistry:
    @staticmethod
    def add(locale: str, key: str, value: str) -> None:
        _I18N.setdefault(locale, {})[key] = value

    @staticmethod
    def get_locale(locale: str) -> dict[str, str]:
        return dict(_I18N.get(locale, {}))

    @staticmethod
    def all() -> dict[str, dict[str, str]]:
        return {loc: dict(d) for loc, d in _I18N.items()}


def get_i18n(locale: str) -> dict[str, str]:
    return I18nRegistry.get_locale(locale)
