"""Good Weighing Practice rule engine.

A trimmed-down placeholder for the GWP validation that runs in production —
it checks the reading is within the device's calibrated range and flags
anything that exceeds the maximum permissible error (MPE) for the load.
"""

from decimal import Decimal

# Maximum permissible error per the OIML R76 table, simplified to four
# load bands. Real production data lives in a profile table keyed by
# device model + calibration certificate.
_MPE_TABLE = [
    (Decimal("0"),        Decimal("50"),     Decimal("0.10")),
    (Decimal("50"),       Decimal("200"),    Decimal("0.20")),
    (Decimal("200"),      Decimal("1000"),   Decimal("0.50")),
    (Decimal("1000"),     Decimal("10000"),  Decimal("2.00")),
]


def mpe_for(load_kg: Decimal) -> Decimal:
    for lo, hi, mpe in _MPE_TABLE:
        if lo <= load_kg < hi:
            return mpe
    return _MPE_TABLE[-1][2]


def passes_gwp(reference_kg: Decimal, measured_kg: Decimal) -> bool:
    return abs(measured_kg - reference_kg) <= mpe_for(reference_kg)
