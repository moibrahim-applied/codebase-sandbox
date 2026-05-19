from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, condecimal


class WeighEvent(BaseModel):
    """A single weighing reading from a FreeWeigh device."""

    device_id: str = Field(..., min_length=4, max_length=64)
    operator_id: str = Field(..., min_length=2, max_length=64)
    mass_kg: condecimal(gt=0, le=10_000, max_digits=10, decimal_places=4)
    unit: Literal["kg", "g", "lb", "oz"] = "kg"
    recipe_id: str | None = None
    measured_at: datetime

    def to_audit_payload(self) -> dict:
        return {
            "device_id": self.device_id,
            "operator_id": self.operator_id,
            "mass_kg": str(self.mass_kg),
            "unit": self.unit,
            "recipe_id": self.recipe_id,
            "measured_at": self.measured_at.isoformat(),
        }


class CalibrationEvent(BaseModel):
    device_id: str = Field(..., min_length=4, max_length=64)
    operator_id: str = Field(..., min_length=2, max_length=64)
    reference_kg: condecimal(gt=0, le=10_000, max_digits=10, decimal_places=4)
    measured_kg: condecimal(gt=0, le=10_000, max_digits=10, decimal_places=4)
    performed_at: datetime
    notes: str | None = Field(default=None, max_length=1024)


class AuditRecord(BaseModel):
    id: str
    kind: Literal["weigh", "calibrate"]
    payload: dict
    recorded_at: datetime
