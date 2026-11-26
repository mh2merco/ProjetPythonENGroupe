"""Commande velo status : résumé du réseau en temps réel."""

import argparse
from dataclasses import dataclass
from datetime import datetime

from velo.config import Config, network_folder
from velo.gbfs import fetch_snapshot, load_network_name, load_stations
from velo.models import Snapshot, Station
from velo.refresh import warn_if_outdated
from velo.states import is_empty, is_full, is_out_of_service


@dataclass(frozen=True)
class NetworkSummary:
    """Chiffres globaux du réseau à un instant donné."""

    name: str
    last_updated: datetime
    total: int
    in_service: int
    out_of_service: int
    empty: int
    full: int
    bikes: int
    docks: int

    @property
    def fill_rate(self) -> float:
        """Part des emplacements occupés par un vélo."""
        total = self.bikes + self.docks
        return self.bikes / total if total else 0.0


def load_current(config: Config) -> tuple[str, Snapshot, dict[str, Station]]:
    """Nom du réseau, état actuel téléchargé et stations connues."""
    folder = network_folder(config)
    warn_if_outdated(config)
    stations = load_stations(folder)
    snapshot = fetch_snapshot(config["network"]["gbfs_url"])
    return load_network_name(folder), snapshot, stations


def summarize(name: str, snapshot: Snapshot, stations: dict[str, Station]) -> NetworkSummary:
    """Calcule le résumé du réseau à partir d'un relevé."""
    statuses = [s for s in snapshot.statuses if s.station_id in stations]
    working = [s for s in statuses if not is_out_of_service(s)]
    return NetworkSummary(
        name=name,
        last_updated=snapshot.last_updated,
        total=len(stations),
        in_service=len(working),
        out_of_service=len(statuses) - len(working),
        empty=sum(1 for s in working if is_empty(s)),
        full=sum(1 for s in working if is_full(s)),
        bikes=sum(s.bikes for s in working),
        docks=sum(s.docks for s in working),
    )


def format_summary(summary: NetworkSummary) -> str:
    """Texte du résumé, réutilisé par le tableau de bord."""
    return "\n".join(
        [
            f"Stations   en service {summary.in_service} / {summary.total}"
            f"   hors service {summary.out_of_service}",
            f"           vides {summary.empty}   pleines {summary.full}",
            f"Vélos      disponibles {summary.bikes}   places libres {summary.docks}",
            f"           taux de remplissage {summary.fill_rate * 100:.0f} %",
        ]
    )


def run(args: argparse.Namespace, config: Config) -> int:
    """Affiche le résumé de l'état actuel du réseau."""
    name, snapshot, stations = load_current(config)
    print(f"{name} - données du {snapshot.last_updated:%d/%m/%Y à %H:%M}\n")
    print(format_summary(summarize(name, snapshot, stations)))
    return 0
