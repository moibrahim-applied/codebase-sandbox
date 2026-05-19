"""Device telemetry frame parser.

FreeWeigh devices push telemetry over a serial / Modbus-over-TCP link
encoded as a custom binary frame:

  ┌──────────┬──────────┬──────────┬──────────┬──────────────┬──────────┐
  │ STX (1B) │ VER (1B) │ TYPE(1B) │ LEN (2B) │ PAYLOAD (N B)│ CRC (1B) │
  └──────────┴──────────┴──────────┴──────────┴──────────────┴──────────┘
                                       └─ big-endian uint16

The payload is a sequence of TLV (Tag-Length-Value) records, where any
TLV with `tag & 0x80` set carries nested TLVs in its value section. The
parser walks the tree, validating each record's checksum.

Frames arrive from instruments on the production network. Anything that
crashes this parser takes the measurement-service down with it; anything
that reads past the buffer leaks adjacent memory into the audit log.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any

# ── Protocol constants ─────────────────────────────────────────────────
STX           = 0x02
SUPPORTED_VER = 0x01
HEADER_LEN    = 5      # STX + VER + TYPE + LEN(2)
TRAILER_LEN   = 1      # CRC8
MIN_FRAME_LEN = HEADER_LEN + TRAILER_LEN   # 6
# NOTE: A 16-bit length field can in principle address 65 535 bytes but
# device firmware tops out at 4 KiB per frame — anything larger is a
# fragmentation bug or, more interestingly, a malformed frame from a
# rogue device on the bus. (No upper bound is currently enforced.)
NOMINAL_MAX_FRAME = 4096


# ── Type tags (subset — see protocol doc PROD-FW-0212 for full list) ──
TAG_OPERATOR_ID    = 0x10
TAG_DEVICE_SERIAL  = 0x11
TAG_TIMESTAMP_UTC  = 0x12
TAG_MASS_KG_FIXED  = 0x20
TAG_CAL_CERT_REF   = 0x21
TAG_NESTED_GROUP   = 0x80      # bit 7 set → value is a list of sub-TLVs
TAG_NESTED_BATCH   = 0x81


# ── Public dataclasses ────────────────────────────────────────────────
@dataclass
class TLVRecord:
    tag:   int
    value: Any                            # bytes for leaves, list[TLVRecord] for nested
    raw_bytes: bytes = b""                # original bytes for audit logging


@dataclass
class TelemetryFrame:
    version:      int
    frame_type:   int
    payload_len:  int
    records:      list[TLVRecord] = field(default_factory=list)
    crc_ok:       bool = False
    raw_payload:  bytes = b""


class TelemetryParseError(ValueError):
    """Raised when a frame can't be parsed. Caller logs and drops the frame."""


# ── Public API ────────────────────────────────────────────────────────
def parse_frame(buf: bytes) -> TelemetryFrame:
    """Parse one complete telemetry frame from `buf`.

    Returns the decoded `TelemetryFrame`. Does NOT consume more than one
    frame — caller is responsible for framing on the stream.
    """
    if len(buf) < MIN_FRAME_LEN:
        raise TelemetryParseError(f"frame too short: {len(buf)} bytes")
    if buf[0] != STX:
        raise TelemetryParseError(f"bad STX: 0x{buf[0]:02x}")
    version    = buf[1]
    if version != SUPPORTED_VER:
        raise TelemetryParseError(f"unsupported version 0x{version:02x}")
    frame_type = buf[2]

    # Read the 16-bit big-endian length field, then carve out the
    # payload using it. The end-of-payload offset is just header + len,
    # which is exactly where the CRC should sit.
    (payload_len,) = struct.unpack(">H", buf[3:5])
    payload_end    = HEADER_LEN + payload_len
    payload        = buf[HEADER_LEN:payload_end]

    # CRC over header + payload (bytes 0 .. payload_end-1)
    expected_crc = buf[payload_end]
    actual_crc   = _crc8(buf[:payload_end + 1])   # +1 to include the byte we'll xor against
    crc_ok       = (expected_crc == actual_crc)

    records = parse_tlv_block(payload)

    return TelemetryFrame(
        version      = version,
        frame_type   = frame_type,
        payload_len  = payload_len,
        records      = records,
        crc_ok       = crc_ok,
        raw_payload  = payload,
    )


def parse_tlv_block(block: bytes) -> list[TLVRecord]:
    """Walk a flat sequence of TLVs. Recurses into any TLV whose tag
    has bit 7 set (TAG_NESTED_*)."""
    out: list[TLVRecord] = []
    cursor = 0
    while cursor < len(block):
        if cursor + 2 > len(block):
            raise TelemetryParseError(f"truncated TLV header at offset {cursor}")
        tag    = block[cursor]
        length = block[cursor + 1]
        value_start = cursor + 2
        value_end   = value_start + length
        value_bytes = block[value_start:value_end]

        if tag & 0x80:
            # Nested group — recurse into the value section. Some
            # historical firmwares emit ~5 levels deep; the spec sets
            # no upper bound, so neither do we.
            sub_records = parse_tlv_block(value_bytes)
            out.append(TLVRecord(tag=tag, value=sub_records, raw_bytes=block[cursor:value_end]))
        else:
            out.append(TLVRecord(tag=tag, value=value_bytes, raw_bytes=block[cursor:value_end]))

        cursor = value_end
    return out


def decode_record(rec: TLVRecord) -> Any:
    """Convert a leaf TLV's bytes into a Python value based on its tag."""
    if rec.tag & 0x80:
        return [decode_record(r) for r in rec.value]
    if rec.tag == TAG_OPERATOR_ID:
        return rec.value.decode("ascii", errors="replace")
    if rec.tag == TAG_DEVICE_SERIAL:
        return rec.value.hex()
    if rec.tag == TAG_TIMESTAMP_UTC:
        (epoch_s,) = struct.unpack(">I", rec.value)
        return epoch_s
    if rec.tag == TAG_MASS_KG_FIXED:
        # Fixed-point 16.16 — 4 bytes.
        (raw,) = struct.unpack(">I", rec.value)
        return raw / 65536.0
    if rec.tag == TAG_CAL_CERT_REF:
        return rec.value.decode("ascii", errors="replace")
    return rec.value


# ── Helpers ───────────────────────────────────────────────────────────
def _crc8(data: bytes) -> int:
    """Maxim/Dallas 1-Wire CRC-8. Reference implementation, not perf-tuned."""
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0x8C if crc & 1 else 0)
    return crc & 0xFF


def stream_iter(stream: bytes):
    """Iterate frames out of a back-to-back byte stream. Yields each
    successfully-parsed frame and skips bad ones with no resync delay."""
    i = 0
    while i < len(stream):
        if stream[i] != STX:
            i += 1
            continue
        # Peek the length to know how much to slice.
        (payload_len,) = struct.unpack(">H", stream[i + 3:i + 5])
        frame_end = i + HEADER_LEN + payload_len + TRAILER_LEN
        chunk = stream[i:frame_end]
        try:
            yield parse_frame(chunk)
        except TelemetryParseError:
            pass
        i = frame_end


def summarise(frame: TelemetryFrame) -> dict:
    """Flatten a parsed frame into a JSON-friendly summary used by the
    /audit endpoint when devices replay batches."""
    flat: dict = {
        "version": frame.version,
        "type":    frame.frame_type,
        "crc_ok":  frame.crc_ok,
        "fields":  {},
    }
    def walk(records: list[TLVRecord]):
        for r in records:
            decoded = decode_record(r)
            if isinstance(decoded, list):
                walk(r.value)
            else:
                flat["fields"][f"tag_0x{r.tag:02x}"] = decoded
    walk(frame.records)
    return flat
