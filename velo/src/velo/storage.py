"""Écriture des relevés dans les fichiers CSV de l'historique (un fichier par jour)."""

import csv
from datetime import date, datetime
from pathlib import Path

from velo.models import Snapshot

COLUMNS = [
    "timestamp",
    "station_id",
    "bikes",
    "docks",
    "is_installed",
    "is_renting",
    "is_returning",
    "last_reported",
]


def iso(moment: datetime) -> str:
    """Date ISO 8601 en heure locale avec décalage : 2026-11-18T08:14:00+01:00."""
    return moment.astimezone().isoformat(timespec="seconds")


def day_file(folder: Path, day: date) -> Path:
    """Fichier CSV d'un jour : <folder>/AAAA-MM-JJ.csv."""
    return folder / f"{day.isoformat()}.csv"


def append_snapshot(folder: Path, snapshot: Snapshot) -> Path:
    """Ajoute un relevé au CSV de son jour, en créant le fichier et l'en-tête si besoin."""
    moment = snapshot.last_updated.astimezone()
    path = day_file(folder, moment.date())
    folder.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(COLUMNS)
        for status in snapshot.statuses:
            writer.writerow(
                [
                    iso(moment),
                    status.station_id,
                    status.bikes,
                    status.docks,
                    str(status.is_installed).lower(),
                    str(status.is_renting).lower(),
                    str(status.is_returning).lower(),
                    iso(status.last_reported),
                ]
            )
    return path


def last_timestamp(folder: Path) -> datetime | None:
    """Date du dernier relevé enregistré, pour ne pas l'enregistrer deux fois."""
    files = sorted(folder.glob("*.csv"))
    if not files:
        return None
    lines = files[-1].read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return None
    try:
        return datetime.fromisoformat(lines[-1].split(",")[0])
    except ValueError:
        return None