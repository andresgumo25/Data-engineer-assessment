import pytest
import json
from ingest_sqlite import parse_semi_struct, _to_bool_int


def test_parse_json_list():
    s = "['Python', 'SQL']"
    out = parse_semi_struct(s)
    assert out is not None
    arr = json.loads(out)
    assert isinstance(arr, list)
    assert 'Python' in arr


def test_parse_json_string():
    s = '["A","B"]'
    out = parse_semi_struct(s)
    assert json.loads(out) == ["A", "B"]


def test_parse_none():
    assert parse_semi_struct('') is None
    assert parse_semi_struct(None) is None


def test_to_bool_int():
    assert _to_bool_int('true') == 1
    assert _to_bool_int('False') == 0
    assert _to_bool_int(True) == 1
    assert _to_bool_int(False) == 0
    assert _to_bool_int('yes') == 1
    assert _to_bool_int('0') == 0
    assert _to_bool_int('unexpected') is None
