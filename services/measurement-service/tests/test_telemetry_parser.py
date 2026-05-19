"""Regression tests for the internal-finding bounds-check patch.

Reproduces the original buffer over-read + stack overflow inputs and
asserts the patched parser refuses them cleanly instead of crashing or
leaking memory.
"""
import struct

import pytest

from app.telemetry_parser import (
    MAX_FRAME_SIZE,
    MAX_TLV_DEPTH,
    TelemetryParseError,
    parse_frame,
    parse_tlv_block,
    stream_iter,
)


def _frame(payload: bytes, *, version: int = 1, ftype: int = 0) -> bytes:
    """Build a well-formed frame around `payload`."""
    header = bytes([0x02, version, ftype]) + struct.pack(">H", len(payload))
    body   = header + payload
    # CRC is the Maxim 1-Wire CRC-8 of header + payload.
    crc = 0
    for b in body:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0x8C if crc & 1 else 0)
    return body + bytes([crc & 0xFF])


def test_parse_frame_rejects_oversized_length():
    """The length field can address 65 535 bytes but real firmware tops
    out at MAX_FRAME_SIZE. Anything bigger is malformed."""
    header  = bytes([0x02, 0x01, 0x00]) + struct.pack(">H", MAX_FRAME_SIZE + 1)
    payload = b"\x00" * 100   # smaller than the lying header
    trailer = b"\x00"
    bogus   = header + payload + trailer
    with pytest.raises(TelemetryParseError, match="MAX_FRAME_SIZE"):
        parse_frame(bogus)


def test_parse_frame_rejects_length_past_buffer():
    """Pre-patch this would have buf[payload_end] read past the wire
    buffer, leaking adjacent memory into the audit log."""
    header  = bytes([0x02, 0x01, 0x00]) + struct.pack(">H", 32)
    payload = b"\x00" * 5    # header lies; buffer is short
    trailer = b"\x00"
    bogus   = header + payload + trailer
    with pytest.raises(TelemetryParseError, match="extends past buffer"):
        parse_frame(bogus)


def test_parse_tlv_block_caps_recursion():
    """Build a payload with MAX_TLV_DEPTH + 1 nested groups and confirm
    the parser refuses cleanly instead of hitting Python's recursion
    limit."""
    block = b""
    inner = b"\x10\x01A"
    for _ in range(MAX_TLV_DEPTH + 1):
        block = bytes([0x80, len(inner)]) + inner
        inner = block
    with pytest.raises(TelemetryParseError, match="MAX_TLV_DEPTH"):
        parse_tlv_block(block)


def test_parse_tlv_block_rejects_length_past_block():
    """Pre-patch the slice would silently truncate while cursor advanced,
    corrupting the next record. Now it raises."""
    bogus_block = bytes([0x10, 0x40]) + b"AB"   # length claims 64, body has 2
    with pytest.raises(TelemetryParseError, match="runs past block"):
        parse_tlv_block(bogus_block)


def test_stream_iter_handles_truncated_tail():
    """A short tail used to raise inside struct.unpack with a confusing
    message; now we just stop iterating cleanly."""
    truncated = b"\x02\x01\x00\x00"   # 4 bytes — not enough for the LEN
    out = list(stream_iter(truncated))
    assert out == []


def test_parse_frame_roundtrip_known_good():
    """A valid frame with one OPERATOR_ID TLV still parses fine after
    the patch."""
    payload = bytes([0x10, 0x04]) + b"op42"
    frame   = parse_frame(_frame(payload))
    assert frame.version == 1
    assert len(frame.records) == 1
    assert frame.records[0].tag == 0x10
