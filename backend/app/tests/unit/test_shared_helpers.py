"""Unit tests for shared utility functions."""
from app.shared.helpers import convert_to_uuid


def test_convert_to_uuid_truncates():
    """Test that long hex strings are truncated to 32 chars for UUID format."""
    hex_hash = "a" * 64
    out = convert_to_uuid(hex_hash)
    assert out == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_convert_to_uuid_pads_short_value():
    """Test that short hex strings are padded with zeros to 32 chars."""
    hex_hash = "123"
    out = convert_to_uuid(hex_hash)
    assert out == "12300000-0000-0000-0000-000000000000"

