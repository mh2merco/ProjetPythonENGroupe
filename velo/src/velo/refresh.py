"""Commande velo refresh : mise à jour des données qui changent rarement."""

import logging
import time

from velo.config import Config, network_folder

logger = logging.getLogger(__name__)

SECONDS_PER_DAY = 86400


def warn_if_outdated(config: Config) -> None:
    """Avertit si station_information.json est plus vieux que refresh.max_age_days."""
    path = network_folder(config) / "station_information.json"
    if not path.exists():
        return
    age_days = (time.time() - path.stat().st_mtime) / SECONDS_PER_DAY
    if age_days > config["refresh"]["max_age_days"]:
        logger.warning(
            "données de référence vieilles de %d jours : lancez 'velo refresh'", age_days
        )
