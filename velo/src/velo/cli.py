"""Point d'entrée de la commande velo : analyse des arguments et aiguillage."""

import argparse
import importlib
import logging
import sys
from collections.abc import Callable
from datetime import date, datetime

from velo.config import Config, load_config, network_folder
from velo.errors import VeloError
from velo.logs import setup_logging

logger = logging.getLogger(__name__)

COMMANDS = {
    "refresh": "velo.refresh",
    "status": "velo.status",
    "station": "velo.stations",
    "favorites": "velo.favorites",
    "alerts": "velo.alerts",
    "dashboard": "velo.dashboard",
    "collect": "velo.collect",
    "history": "velo.history",
    "query": "velo.query",
}

METRICS = ("avg_bikes", "avg_docks", "empty_rate", "full_rate")


def date_arg(text: str) -> date:
    """Type argparse : une date AAAA-MM-JJ."""
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"date invalide '{text}' (AAAA-MM-JJ)") from None


def datetime_arg(text: str) -> datetime:
    """Type argparse : une date AAAA-MM-JJ, éventuellement suivie de HH:MM."""
    try:
        return datetime.fromisoformat(text).astimezone()
    except ValueError:
        message = f"date invalide '{text}' (AAAA-MM-JJ ou \"AAAA-MM-JJ HH:MM\")"
        raise argparse.ArgumentTypeError(message) from None


def build_parser() -> argparse.ArgumentParser:
    """Déclare toutes les commandes et leurs options."""
    parser = argparse.ArgumentParser(prog="velo", description="Vélos en libre-service")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="prépare l'outil")
    p.add_argument("--force", action="store_true", help="écrase la configuration")
    sub.add_parser("refresh", help="met à jour les données qui changent rarement")
    sub.add_parser("status", help="résumé du réseau en temps réel")

    p = sub.add_parser("station", help="chercher ou lister les stations")
    actions = p.add_subparsers(dest="action", required=True)
    actions.add_parser("search", help="chercher par le nom").add_argument("text")
    actions.add_parser("list", help="lister toutes les stations")

    p = sub.add_parser("favorites", help="stations favorites")
    actions = p.add_subparsers(dest="action")
    actions.add_parser("add", help="ajouter un favori").add_argument("station_id")
    actions.add_parser("remove", help="retirer un favori").add_argument("station_id")

    p = sub.add_parser("alerts", help="stations vides, pleines ou hors service")
    p.add_argument("--low-bikes", type=int, help="seuil de vélos (presque vide)")
    p.add_argument("--low-docks", type=int, help="seuil de places (presque pleine)")

    p = sub.add_parser("dashboard", help="tableau de bord en temps réel")
    p.add_argument("--refresh", type=int, help="secondes entre deux mises à jour")

    p = sub.add_parser("collect", help="enregistrer l'état du réseau")
    p.add_argument("--interval", type=int, help="secondes entre deux relevés")
    stop = p.add_mutually_exclusive_group()
    stop.add_argument("--duration", help="durée, par exemple 3h ou 1h30m")
    stop.add_argument("--until", help='date de fin "AAAA-MM-JJ HH:MM"')
    stop.add_argument("--once", action="store_true", help="un seul relevé")

    p = sub.add_parser("history", help="périodes enregistrées")
    p.add_argument("--from", dest="date_from", type=date_arg)
    p.add_argument("--to", dest="date_to", type=date_arg)

    p = sub.add_parser("query", help="analyser l'historique")
    p.add_argument("--metric", nargs="+", required=True, choices=METRICS)
    p.add_argument("--date", type=date_arg)
    p.add_argument("--from", dest="date_from", type=datetime_arg)
    p.add_argument("--to", dest="date_to", type=datetime_arg)
    p.add_argument("--period", nargs="+", type=int)
    p.add_argument("--days", nargs="+", help="weekdays, weekend ou des jours")
    p.add_argument("--hours", help="plage horaire, par exemple 7-9")
    p.add_argument("--station", help="identifiant d'une station")
    p.add_argument("--by", choices=("station", "hour", "weekday", "day"))
    p.add_argument("--top", type=int)
    return parser


def load_handler(command: str) -> Callable[[argparse.Namespace, Config], int]:
    """Importe le module de la commande et renvoie sa fonction run."""
    module_name = COMMANDS[command]
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise
        raise VeloError(f"la commande '{command}' n'est pas encore disponible") from exc
    return module.run


def main(argv: list[str] | None = None) -> int:
    """Lance la commande demandée et renvoie le code de sortie."""
    args = build_parser().parse_args(argv)
    setup_logging("INFO", None)
    try:
        if args.command == "init":
            from velo.init import run_init

            return run_init(args.force)
        config = load_config()
        setup_logging(config["logging"]["level"], network_folder(config) / "velo.log")
        return load_handler(args.command)(args, config)
    except VeloError as exc:
        logger.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130
    except Exception as exc:
        logger.debug("Erreur inattendue", exc_info=True)
        logger.error("erreur inattendue (%s), détails dans velo.log", exc)
        return 1