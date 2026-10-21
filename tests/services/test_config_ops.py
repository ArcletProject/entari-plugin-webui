from __future__ import annotations

import pytest


@pytest.fixture(name="ops")
def _ops():
    from entari_plugin_webui.services import config_ops

    return config_ops


def test_diff_scalar_replace(ops):
    result = ops.diff({"a": 1}, {"a": 2})
    assert result.ops == [ops.Op("replace", ("a",), 2)]


def test_diff_dict_add_remove(ops):
    result = ops.diff({"a": 1, "b": 2}, {"a": 1, "c": 3})
    assert ops.Op("remove", ("b",)) in result.ops
    assert ops.Op("add", ("c",), 3) in result.ops


def test_apply_list_remove_keeps_dict_identity(ops):
    old = [1, {"a": 2}]
    kept = old[1]
    target = old
    result = ops.diff(old, [{"a": 2}])
    ops.apply_ops(target, result.ops)
    assert target == [{"a": 2}]
    assert target[0] is kept


def test_apply_dict_field_change_keeps_dict_identity(ops):
    old = [{"a": 1}, {"b": 2}]
    target = old
    result = ops.diff(old, [{"a": 9}, {"b": 2}])
    ops.apply_ops(target, result.ops)
    assert target == [{"a": 9}, {"b": 2}]
    assert target[0] is old[0]


def test_apply_list_insert_and_remove(ops):
    old = [{"id": "a"}, {"id": "b"}]
    kept = old[1]
    target = old
    result = ops.diff(old, [{"id": "b"}, {"id": "c"}])
    ops.apply_ops(target, result.ops)
    assert target == [{"id": "b"}, {"id": "c"}]
    assert target[0] is kept


def test_strip_new_defaults_drops_new_default_keys(ops):
    raw = {"prefix": ["/"]}
    desired = {"prefix": ["/"], "nickname": "", "cmd_count": 4096}
    effective = {"prefix": ["/"], "nickname": "", "cmd_count": 4096}
    assert ops.strip_new_defaults(raw, desired, effective) == {"prefix": ["/"]}


def test_strip_new_defaults_keeps_existing_defaults(ops):
    raw = {"nickname": ""}
    desired = {"nickname": ""}
    effective = {"nickname": ""}
    assert ops.strip_new_defaults(raw, desired, effective) == {"nickname": ""}


def test_strip_new_defaults_nested(ops):
    raw = {"network": {}}
    desired = {"network": {"proxy": "", "timeout": 30}}
    effective = {"network": {"proxy": "", "timeout": 30}}
    assert ops.strip_new_defaults(raw, desired, effective) == {"network": {}}


def test_strip_new_defaults_drops_nested_defaults_for_new_object(ops):
    raw = {}
    desired = {"network": {"proxy": "", "timeout": 30}}
    effective = {"network": {"proxy": "", "timeout": 30}}
    assert ops.strip_new_defaults(raw, desired, effective) == {}


def test_strip_new_defaults_drops_partial_nested_default_for_new_object(ops):
    raw = {}
    desired = {"network": {"proxy": ""}}
    effective = {"network": {"proxy": "", "timeout": 30}}
    assert ops.strip_new_defaults(raw, desired, effective) == {}


def test_remap_path_drops_removed_and_shifts_list_indices(ops):
    result = ops.diff({"items": [{"a": 1}, {"b": 2}]}, {"items": [{"b": 2}]})
    remap = ops.make_remapper(result)
    assert remap(("items", 0, "a")) is None
    assert remap(("items", 1, "b")) == ("items", 0, "b")
    assert remap(("other", "x")) == ("other", "x")
