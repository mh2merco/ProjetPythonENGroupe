"""Commande velo init."""

import logging

from velo.config import config_path, load_config, network_folder, write_default_config
from velo.errors import VeloError
from velo.gbfs import download_rare_feeds
from velo.logs import setup_logging

logger = logging.getLogger(__name__)


def run_init(force: bool) -> int:
    """Crée la configuration, le dossier de données et teste la connexion."""
    path = config_path()
    if write_default_config(path, force):
        print(f"Configuration créée : {path}")
    else:
        print(f"Configuration existante conservée : {path} (--force pour l'écraser)")
    config = load_config()
    folder = network_folder(config)
    (folder / "history").mkdir(parents=True, exist_ok=True)
    setup_logging(config["logging"]["level"], folder / "velo.log")
    print(f"Dossier de données créé : {folder}")
    name = config["network"]["name"]
    try:
        count = download_rare_feeds(config["network"]["gbfs_url"], folder)
    except VeloError as exc:
        logger.warning("connexion à %s impossible (%s)", name, exc)
        return 0
    print(f"Connexion à {name} : OK ({count} stations)")
    return 0