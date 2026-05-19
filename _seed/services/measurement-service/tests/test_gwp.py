from decimal import Decimal

import pytest

from app.gwp import mpe_for, passes_gwp


def test_mpe_band_low():
    assert mpe_for(Decimal("10")) == Decimal("0.10")


def test_mpe_band_high():
    assert mpe_for(Decimal("4500")) == Decimal("2.00")


@pytest.mark.parametrize(
    "ref,measured,expected",
    [
        (Decimal("10.000"), Decimal("10.05"),  True),   # within 0.10
        (Decimal("10.000"), Decimal("10.20"),  False),  # outside 0.10
        (Decimal("500.00"), Decimal("500.40"), True),
        (Decimal("500.00"), Decimal("500.60"), False),
    ],
)
def test_passes_gwp(ref, measured, expected):
    assert passes_gwp(ref, measured) is expected
