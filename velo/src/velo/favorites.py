"""Commande velo favorites : afficher, ajouter et retirer des stations favorites."""

import argparse
import json
from pathlib import Path

from velo.config import Config, network_folder
from velo.display import table
from velo.errors import VeloError
from velo.gbfs import load_stations
from velo.models import Snapshot, Station
from velo.states import label
from velo.status import load_current

MAX_FAVORITES = 10
HEADERS = ["ID", "Station", "Vélos", "Places", ""]


def favorites_file(folder: Path) -> Path:
    """Fichier des favoris, géré par l'outil dans le dossier du réseau."""
    return folder / "favorites.json"


def load_favorites(folder: Path) -> list[str]:
    """Identifiants des stations favorites, dans l'ordre d'ajout."""
    path = favorites_file(folder)
    if not path.exists():
        return []
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise VeloError(f"fichier des favoris illisible : {path}") from exc
    if not isinstance(content, list):
        raise VeloError(f"fichier des favoris invalide : {path}")
    return [str(station_id) for station_id in content]


def save_favorites(folder: Path, ids: list[str]) -> None:
    """Enregistre la liste des favoris."""
    folder.mkdir(parents=True, exist_ok=True)
    favorites_file(folder).write_text(json.dumps(ids, indent=2), encoding="utf-8")


def add_favorite(folder: Path, station_id: str, stations: dict[str, Station]) -> None:
    """Ajoute une station aux favoris après toutes les vérifications."""
    ids = load_favorites(folder)
    if station_id not in stations:
        raise VeloError(f"station {station_id} inconnue (voir 'velo station search')")
    if station_id in ids:
        raise VeloError(f"la station {station_id} est déjà dans les favoris")
    if len(ids) >= MAX_FAVORITES:
        raise VeloError(
            f"{MAX_FAVORITES} favoris maximum : retirez-en un avec 'velo favorites remove'"
        )
    ids.append(station_id)
    save_favorites(folder, ids)


def remove_favorite(folder: Path, station_id: str) -> None:
    """Retire une station des favoris."""
    ids = load_favorites(folder)
    if station_id not in ids:
        raise VeloError(f"la station {station_id} n'est pas dans les favoris")
    ids.remove(station_id)
    save_favorites(folder, ids)


def favorite_rows(
    ids: list[str],
    stations: dict[str, Station],
    snapshot: Snapshot,
    low_bikes: int,
    low_docks: int,
) -> list[list[object]]:
    """Lignes du tableau des favoris, réutilisées par le tableau de bord."""
    by_id = {status.station_id: status for status in snapshot.statuses}
    rows: list[list[object]] = []
    for station_id in ids:
        name = stations[station_id].name if station_id in stations else "(disparue)"
        status = by_id.get(station_id)
        if status is None:
            rows.append([station_id, name, "-", "-", "sans données"])
        else:
            state = label(status, low_bikes, low_docks)
            rows.append([station_id, name, status.bikes, status.docks, state])
    return rows


def run(args: argparse.Namespace, config: Config) -> int:
    """Exécute velo favorites, velo favorites add ou velo favorites remove."""
    folder = network_folder(config)
    if args.action == "add":
        add_favorite(folder, args.station_id, load_stations(folder))
        print(f"Station {args.station_id} ajoutée aux favoris")
        return 0
    if args.action == "remove":
        remove_favorite(folder, args.station_id)
        print(f"Station {args.station_id} retirée des favoris")
        return 0
    ids = load_favorites(folder)
    if not ids:
        print("Aucun favori. Cherchez une station avec 'velo station search <texte>'")
        print("puis ajoutez-la avec 'velo favorites add <id>'.")
        return 0
    _, snapshot, stations = load_current(config)
    alerts = config["alerts"]
    rows = favorite_rows(ids, stations, snapshot, alerts["low_bikes"], alerts["low_docks"])
    print(table(HEADERS, rows, right={2, 3}))
    return 0