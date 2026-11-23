"""Définition des états d'une station (justifiés dans le README)."""

from velo.models import StationStatus


def is_out_of_service(status: StationStatus) -> bool:
    """Hors service : non installée, ou impossible d'y louer ou d'y rendre un vélo."""
    return not (status.is_installed and status.is_renting and status.is_returning)


def is_empty(status: StationStatus) -> bool:
    """Vide : aucun vélo disponible."""
    return status.bikes == 0


def is_almost_empty(status: StationStatus, low_bikes: int) -> bool:
    """Vide ou presque vide : nombre de vélos inférieur ou égal au seuil."""
    return status.bikes <= low_bikes


def is_full(status: StationStatus) -> bool:
    """Pleine : aucune place libre."""
    return status.docks == 0


def is_almost_full(status: StationStatus, low_docks: int) -> bool:
    """Pleine ou presque pleine : nombre de places inférieur ou égal au seuil."""
    return status.docks <= low_docks


def label(status: StationStatus, low_bikes: int, low_docks: int) -> str:
    """Étiquette courte affichée à côté d'une station."""
    if is_out_of_service(status):
        return "hors service"
    if is_empty(status):
        return "vide"
    if is_almost_empty(status, low_bikes):
        return "presque vide"
    if is_full(status):
        return "pleine"
    if is_almost_full(status, low_docks):
        return "presque pleine"
    return ""
