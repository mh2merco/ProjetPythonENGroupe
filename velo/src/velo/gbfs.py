"""Seul module qui lit le format GBFS (versions 2.x et 3.0)."""

import json
import logging
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from velo.errors import VeloError
from velo.models import Snapshot, Station, StationStatus

logger = logging.getLogger(__name__)

RARE_FEEDS = ("system_information", "station_information", "vehicle_types")
TIMEOUT_SECONDS = 15


def fetch_json(url: str) -> dict[str, Any]:
    """Télécharge une URL et renvoie le JSON, après une première vérification."""
    logger.debug("Téléchargement de %s", url)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            content = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise VeloError(f"réseau indisponible ou réponse illisible : {url}") from exc
    if not isinstance(content, dict) or not isinstance(content.get("data"), dict):
        raise VeloError(f"réponse GBFS invalide (champ 'data' absent) : {url}")
    return content


def discover_feeds(gbfs_url: str) -> dict[str, str]:
    """Lit gbfs.json et renvoie le dictionnaire nom du flux -> URL."""
    data = fetch_json(gbfs_url)["data"]
    if "feeds" not in data:
        languages = [value for value in data.values() if isinstance(value, dict)]
        if not languages or "feeds" not in languages[0]:
            raise VeloError("gbfs.json ne contient aucune liste de flux")
        data = languages[0]
    return {feed["name"]: feed["url"] for feed in data["feeds"]}


def parse_time(value: Any) -> datetime:
    """Convertit une date GBFS (secondes POSIX ou texte ISO 8601) en heure locale."""
    if isinstance(value, int | float) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, tz=UTC).astimezone()
    if isinstance(value, str):
        return datetime.fromisoformat(value).astimezone()
    raise ValueError(f"date invalide : {value!r}")


def text_of(value: Any) -> str:
    """Texte simple (GBFS 2) ou premier texte d'une liste traduite (GBFS 3)."""
    if isinstance(value, list):
        return str(value[0]["text"])
    return str(value)


def download_rare_feeds(gbfs_url: str, folder: Path) -> int:
    """Enregistre les trois flux rares dans folder ; renvoie le nombre de stations."""
    feeds = discover_feeds(gbfs_url)
    folder.mkdir(parents=True, exist_ok=True)
    for name in RARE_FEEDS:
        if name not in feeds:
            logger.info("Flux %s absent de ce réseau", name)
            continue
        content = fetch_json(feeds[name])
        path = folder / f"{name}.json"
        path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
        logger.info("Fichier enregistré : %s", path)
    return len(load_stations(folder))


def read_local(folder: Path, name: str) -> dict[str, Any]:
    """Lit un flux rare déjà enregistré dans le dossier du réseau."""
    path = folder / f"{name}.json"
    if not path.exists():
        raise VeloError(f"fichier {path.name} absent : lancez 'velo refresh'")
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise VeloError(f"fichier {path.name} illisible : lancez 'velo refresh'") from exc
    return content.get("data", {}) if isinstance(content, dict) else {}


def load_network_name(folder: Path) -> str:
    """Nom du réseau, lu dans system_information."""
    try:
        return text_of(read_local(folder, "system_information")["name"])
    except (KeyError, IndexError, TypeError):
        return "Réseau"


def load_stations(folder: Path) -> dict[str, Station]:
    """Stations valides de station_information, rangées par identifiant."""
    stations: dict[str, Station] = {}
    for raw in read_local(folder, "station_information").get("stations", []):
        try:
            station = Station(
                station_id=str(raw["station_id"]),
                name=text_of(raw["name"]),
                lat=float(raw["lat"]),
                lon=float(raw["lon"]),
                capacity=int(raw.get("capacity", 0)),
            )
        except (KeyError, IndexError, TypeError, ValueError):
            logger.warning("station ignorée (données invalides) : %r", raw)
            continue
        stations[station.station_id] = station
    return stations


def parse_status(raw: dict[str, Any]) -> StationStatus:
    """Convertit une entrée de station_status en StationStatus."""
    if "num_bikes_available" in raw:
        bikes = raw["num_bikes_available"]
    else:
        bikes = raw["num_vehicles_available"]
    return StationStatus(
        station_id=str(raw["station_id"]),
        bikes=int(bikes),
        docks=int(raw["num_docks_available"]),
        is_installed=bool(raw["is_installed"]),
        is_renting=bool(raw["is_renting"]),
        is_returning=bool(raw["is_returning"]),
        last_reported=parse_time(raw["last_reported"]),
    )


def fetch_snapshot(gbfs_url: str) -> Snapshot:
    """Télécharge station_status et renvoie le relevé validé."""
    feeds = discover_feeds(gbfs_url)
    if "station_status" not in feeds:
        raise VeloError("ce réseau ne publie pas de flux station_status")
    content = fetch_json(feeds["station_status"])
    statuses = []
    for raw in content["data"].get("stations", []):
        try:
            statuses.append(parse_status(raw))
        except (KeyError, TypeError, ValueError):
            logger.warning("état de station ignoré (données invalides) : %r", raw)
    try:
        last_updated = parse_time(content["last_updated"])
    except (KeyError, ValueError) as exc:
        raise VeloError("station_status : champ last_updated invalide") from exc
    return Snapshot(last_updated, statuses)
