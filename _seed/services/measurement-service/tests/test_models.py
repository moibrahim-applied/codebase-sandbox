from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import CalibrationEvent, WeighEvent


def test_weigh_event_accepts_valid_payload():
    e = WeighEvent(
        device_id="scale-001",
        operator_id="op-42",
        mass_kg=Decimal("12.3450"),
        unit="kg",
        recipe_id="recipe-7",
        measured_at=datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc),
    )
    payload = e.to_audit_payload()
    assert payload["mass_kg"] == "12.3450"
    assert payload["measured_at"].startswith("2026-05-18")


def test_weigh_event_rejects_zero_mass():
    with pytest.raises(ValidationError):
        WeighEvent(
            device_id="scale-001",
            operator_id="op-42",
            mass_kg=Decimal("0"),
            measured_at=datetime.now(timezone.utc),
        )


def test_calibration_notes_max_length():
    too_long = "x" * 2000
    with pytest.raises(ValidationError):
        CalibrationEvent(
            device_id="scale-001",
            operator_id="op-42",
            reference_kg=Decimal("100"),
            measured_kg=Decimal("100.01"),
            performed_at=datetime.now(timezone.utc),
            notes=too_long,
        )
