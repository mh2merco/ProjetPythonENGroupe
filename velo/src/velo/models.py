"""Objets manipulés par tout l'outil, indépendants du format GBFS."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Station:
    """Station du réseau (informations qui changent rarement)."""

    station_id: str
    name: str
    lat: float
    lon: float
    capacity: int


@dataclass(frozen=True)
class StationStatus:
    """État d'une station à un instant donné."""

    station_id: str
    bikes: int
    docks: int
    is_installed: bool
    is_renting: bool
    is_returning: bool
    last_reported: datetime


@dataclass(frozen=True)
class Snapshot:
    """Relevé : état de toutes les stations à un instant donné."""

    last_updated: datetime
    statuses: list[StationStatus]
