from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from ruamel.yaml import CommentedMap, CommentedSeq

PathPart = str | int
Path = tuple[PathPart, ...]

_IDENTITY_KEYS = ("$path", "key", "name", "type", "id")


@dataclass(frozen=True)
class Op:
    kind: Literal["add", "remove", "replace", "move"]
    path: Path
    value: Any = None
    to: int | None = None


@dataclass
class DiffResult:
    ops: list[Op] = field(default_factory=list)
    remap: dict[Path, Path | None] = field(default_factory=dict)


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _equal(left: Any, right: Any) -> bool:
    return left == right


def _wrap(value: Any) -> Any:
    if isinstance(value, (CommentedMap, CommentedSeq)):
        return value
    if isinstance(value, Mapping):
        return CommentedMap({key: _wrap(item) for key, item in value.items()})
    if isinstance(value, list):
        return CommentedSeq([_wrap(item) for item in value])
    return value


def diff(old: Any, new: Any) -> DiffResult:
    result = DiffResult()
    _diff_node(old, new, (), result)
    return result


def _diff_node(old: Any, new: Any, path: Path, result: DiffResult) -> None:
    if _is_mapping(old) and _is_mapping(new):
        _diff_mapping(old, new, path, result)
    elif _is_sequence(old) and _is_sequence(new):
        _diff_sequence(old, new, path, result)
    elif not _equal(old, new):
        result.ops.append(Op("replace", path, new))
        result.remap[path] = None


def _diff_mapping(old: Mapping, new: Mapping, path: Path, result: DiffResult) -> None:
    for key in old:
        if key not in new:
            result.ops.append(Op("remove", (*path, key)))
            result.remap[(*path, key)] = None
    for key, value in new.items():
        if key not in old:
            result.ops.append(Op("add", (*path, key), value))
            continue
        _diff_node(old[key], value, (*path, key), result)


def _identity_key(value: Any) -> tuple[str, Any] | None:
    if not _is_mapping(value):
        return None
    for key in _IDENTITY_KEYS:
        if key not in value:
            continue
        candidate = value[key]
        if isinstance(candidate, (str, int, float, bool)) or candidate is None:
            return key, candidate
    return None


def _match_sequences(old: Sequence, new: Sequence) -> list[tuple[int, int]]:
    old_indices = list(range(len(old)))
    new_indices = list(range(len(new)))
    matches: list[tuple[int, int]] = []

    # 1. stable identity keys
    for key in _IDENTITY_KEYS:
        old_values: dict[Any, int] = {}
        new_values: dict[Any, int] = {}
        for index in old_indices:
            value = old[index]
            if _is_mapping(value) and key in value and not isinstance(value[key], (dict, list)):
                old_values.setdefault(value[key], index)
        for index in new_indices:
            value = new[index]
            if _is_mapping(value) and key in value and not isinstance(value[key], (dict, list)):
                new_values.setdefault(value[key], index)
        for value, old_index in list(old_values.items()):
            if value not in new_values:
                continue
            new_index = new_values[value]
            if old_index in old_indices and new_index in new_indices:
                matches.append((old_index, new_index))
                old_indices.remove(old_index)
                new_indices.remove(new_index)

    # 2. same-length lists: pair by position to catch in-place field edits
    if len(old) == len(new) and not matches:
        matches.extend(zip(old_indices, new_indices, strict=False))
        return matches

    # 3. LCS for the remaining elements, deep equality only
    old_rest = [old[index] for index in old_indices]
    new_rest = [new[index] for index in new_indices]
    table = [[0] * (len(new_rest) + 1) for _ in range(len(old_rest) + 1)]
    for i in range(len(old_rest) - 1, -1, -1):
        for j in range(len(new_rest) - 1, -1, -1):
            if _equal(old_rest[i], new_rest[j]):
                table[i][j] = table[i + 1][j + 1] + 1
            else:
                table[i][j] = max(table[i + 1][j], table[i][j + 1])
    i = j = 0
    while i < len(old_rest) and j < len(new_rest):
        if _equal(old_rest[i], new_rest[j]):
            matches.append((old_indices[i], new_indices[j]))
            i += 1
            j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    matches.sort()
    return matches


def _diff_sequence(old: Sequence, new: Sequence, path: Path, result: DiffResult) -> None:
    if _equal(old, new):
        return

    matches = _match_sequences(old, new)
    old_to_new = dict(matches)
    new_to_old = {new_index: old_index for old_index, new_index in matches}

    for old_index, new_index in matches:
        if new_index >= len(new):
            continue
        result.remap[(*path, old_index)] = (*path, new_index)
        _diff_node(old[old_index], new[new_index], (*path, old_index), result)

    for old_index in range(len(old) - 1, -1, -1):
        if old_index not in old_to_new:
            result.ops.append(Op("remove", (*path, old_index)))
            result.remap[(*path, old_index)] = None

    current = [index for index in range(len(old)) if index in old_to_new]
    desired = [new_to_old[new_index] for new_index in sorted(new_to_old)]
    for target, old_index in enumerate(desired):
        current_index = current.index(old_index)
        if current_index != target:
            result.ops.append(Op("move", (*path, current_index), to=target))
            current.pop(current_index)
            current.insert(target, old_index)

    for new_index in range(len(new)):
        if new_index in new_to_old:
            continue
        result.ops.append(Op("add", (*path, new_index), new[new_index]))


def _resolve(root: Any, path: Path) -> Any:
    node = root
    for part in path:
        node = node[part]
    return node


def apply_ops(root: Any, ops: list[Op]) -> None:
    for op in ops:
        parent = _resolve(root, op.path[:-1])
        key = op.path[-1]
        if op.kind == "add":
            if isinstance(parent, MutableSequence):
                parent.insert(int(key), _wrap(op.value))
            else:
                parent[key] = _wrap(op.value)
        elif op.kind == "remove":
            del parent[key]
        elif op.kind == "replace":
            parent[key] = _wrap(op.value)
        elif op.kind == "move":
            item = parent.pop(int(key))
            parent.insert(int(op.to), item)
        else:  # pragma: no cover - guarded by Literal
            raise ValueError(f"unknown op: {op.kind}")


def _strip_mapping(raw: Mapping, desired: Mapping, effective: Mapping) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in desired.items():
        if isinstance(key, str) and key.startswith("$"):
            out[key] = value
            continue
        if key not in raw:
            nested_effective = effective.get(key)
            if _is_mapping(value) and _is_mapping(nested_effective):
                stripped = _strip_mapping({}, value, nested_effective)
                if stripped:
                    out[key] = stripped
                continue
            if key in effective and _equal(value, effective[key]):
                continue
            out[key] = value
            continue
        if _is_mapping(value) and _is_mapping(raw[key]):
            nested_effective = effective.get(key)
            out[key] = _strip_mapping(
                raw[key],
                value,
                nested_effective if _is_mapping(nested_effective) else {},
            )
        else:
            out[key] = value
    return out


def strip_new_defaults(raw: Any, desired: Any, effective: Any) -> Any:
    if _is_mapping(desired):
        return _strip_mapping(raw if _is_mapping(raw) else {}, desired, effective if _is_mapping(effective) else {})
    return desired


def make_remapper(result: DiffResult):
    def remap(path: Path) -> Path | None:
        best: tuple[Path, Path | None] | None = None
        for prefix, mapped in result.remap.items():
            if len(prefix) > len(path) or path[: len(prefix)] != prefix:
                continue
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, mapped)
        if best is None:
            return path
        prefix, mapped = best
        if mapped is None:
            return None
        return (*mapped, *path[len(prefix) :])

    return remap
