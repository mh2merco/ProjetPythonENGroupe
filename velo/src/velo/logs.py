"""Mise en place de la journalisation."""

import logging
from pathlib import Path


def setup_logging(level: str, log_file: Path | None) -> None:
    """Avertissements et erreurs dans la console, journal détaillé dans un fichier."""
    logging.addLevelName(logging.WARNING, "Avertissement")
    logging.addLevelName(logging.ERROR, "Erreur")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(logging.Formatter("%(levelname)s : %(message)s"))
    root.addHandler(console)
    if log_file is None:
        return
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level.upper())
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s : %(message)s"))
    root.addHandler(file_handler)