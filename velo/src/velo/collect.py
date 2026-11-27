"""Commande velo collect : enregistrer l'état du réseau à intervalle régulier."""

import argparse
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from velo.config import Config, check_minimum, network_folder, resolve
from velo.errors import VeloError
from velo.gbfs import fetch_snapshot
from velo.storage import append_snapshot, last_timestamp

logger = logging.getLogger(__name__)

DURATION = re.compile(r"(?:(\d+)h)?(?:(\d+)m(?:in)?)?")


@dataclass
class Report:
    """Bilan de la collecte."""

    count: int = 0
    first: datetime | None = None
    last: datetime | None = None


def parse_duration(text: str) -> timedelta:
    """Convertit « 3h », « 45m » ou « 1h30m » en durée."""
    match = DURATION.fullmatch(text.strip().lower())
    if not match or not any(match.groups()):
        raise VeloError(f"durée invalide '{text}' (exemples : 3h, 45m, 1h30m)")
    hours, minutes = (int(group or 0) for group in match.groups())
    return timedelta(hours=hours, minutes=minutes)


def parse_until(text: str) -> datetime:
    """Convertit « AAAA-MM-JJ HH:MM » en date future, en heure locale."""
    try:
        moment = datetime.strptime(text, "%Y-%m-%d %H:%M").astimezone()
    except ValueError:
        raise VeloError(f"date invalide '{text}' (format \"AAAA-MM-JJ HH:MM\")") from None
    if moment <= datetime.now().astimezone():
        raise VeloError("la date de --until est déjà passée")
    return moment


def compute_end(args: argparse.Namespace) -> datetime | None:
    """Date d'arrêt automatique, ou None pour tourner jusqu'à Ctrl+C."""
    if args.duration:
        return datetime.now().astimezone() + parse_duration(args.duration)
    if args.until:
        return parse_until(args.until)
    return None


def collect_once(url: str, folder: Path, previous: datetime | None, report: Report) -> datetime:
    """Fait un relevé et l'enregistre seulement si sa date last_updated est nouvelle."""
    snapshot = fetch_snapshot(url)
    moment = snapshot.last_updated
    if previous is not None and moment == previous:
        logger.info("Relevé identique au précédent, non enregistré")
        return moment
    path = append_snapshot(folder, snapshot)
    report.count += 1
    report.first = report.first or moment
    report.last = moment
    logger.info("Relevé %s enregistré dans %s", moment.isoformat(), path.name)
    print(f"Relevé n°{report.count} : données de {moment:%H:%M:%S} enregistrées")
    return moment


def format_report(report: Report) -> str:
    """Texte du bilan affiché à la fin de la collecte."""
    if report.first is None or report.last is None:
        return "Bilan : aucun relevé enregistré."
    return (
        f"Bilan : {report.count} relevé(s), "
        f"début {report.first:%d/%m/%Y %H:%M:%S}, fin {report.last:%d/%m/%Y %H:%M:%S}"
    )


def run(args: argparse.Namespace, config: Config) -> int:
    """Lance la collecte jusqu'à la fin prévue ou jusqu'à Ctrl+C."""
    interval = resolve(args.interval, config, "collect", "interval_seconds")
    check_minimum(interval, 60, "--interval")
    end = compute_end(args)
    url = config["network"]["gbfs_url"]
    folder = network_folder(config) / "history"
    report = Report()
    previous = last_timestamp(folder)
    print(f"Collecte toutes les {interval} s dans {folder} (Ctrl+C pour arrêter)")
    try:
        while True:
            started = time.monotonic()
            try:
                previous = collect_once(url, folder, previous, report)
            except VeloError as exc:
                if args.once:
                    raise
                logger.error("%s : nouvel essai au prochain relevé", exc)
            if args.once:
                break
            pause = max(0.0, interval - (time.monotonic() - started))
            now = datetime.now().astimezone()
            if end is not None and now + timedelta(seconds=pause) > end:
                break
            time.sleep(pause)
    except KeyboardInterrupt:
        print("\nCollecte arrêtée (Ctrl+C).")
    print(format_report(report))
    return 0