from datetime import datetime

from velo.display import table
from velo.models import StationStatus
from velo.states import (
    is_almost_empty,
    is_almost_full,
    is_empty,
    is_full,
    is_out_of_service,
    label,
)

NOW = datetime(2026, 11, 16, 12, 5).astimezone()


def make(bikes=5, docks=5, installed=True, renting=True, returning=True):
    return StationStatus("1", bikes, docks, installed, renting, returning, NOW)


def test_out_of_service():
    assert not is_out_of_service(make())
    assert is_out_of_service(make(installed=False))
    assert is_out_of_service(make(renting=False))
    assert is_out_of_service(make(returning=False))


def test_empty_and_full():
    assert is_empty(make(bikes=0)) and not is_empty(make(bikes=1))
    assert is_full(make(docks=0)) and not is_full(make(docks=1))


def test_thresholds_are_inclusive():
    assert is_almost_empty(make(bikes=2), 2)
    assert not is_almost_empty(make(bikes=3), 2)
    assert is_almost_full(make(docks=2), 2)


def test_label_priority():
    assert label(make(bikes=0, renting=False), 2, 2) == "hors service"
    assert label(make(bikes=0), 2, 2) == "vide"
    assert label(make(bikes=1), 2, 2) == "presque vide"