"""Lecture, validation et priorité des réglages de config.yaml."""

import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from velo.errors import VeloError

Config = dict[str, dict[str, Any]]

DEFAULTS: Config = {
    "network": {
        "name": "V'Lille",
        "gbfs_url": "https://media.ilevia.fr/opendata/gbfs.json",
    },
    "data": {"folder": ""},
    "refresh": {"max_age_days": 7},
    "collect": {"interval_seconds": 120},
    "alerts": {"low_bikes": 2, "low_docks": 2},
    "dashboard": {"refresh_seconds": 60},
    "logging": {"level": "INFO"},
}

MINIMUMS = {
    ("refresh", "max_age_days"): 1,
    ("collect", "interval_seconds"): 60,
    ("alerts", "low_bikes"): 0,
    ("alerts", "low_docks"): 0,
    ("dashboard", "refresh_seconds"): 60,
}

LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def config_path() -> Path:
    """Chemin de config.yaml (la variable VELO_CONFIG permet de le changer)."""
    if "VELO_CONFIG" in os.environ:
        return Path(os.environ["VELO_CONFIG"])
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "velo" / "config.yaml"


def default_data_folder() -> Path:
    """Dossier de données par défaut, selon le système."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "velo"


def default_config() -> Config:
    """Copie des valeurs par défaut, avec le dossier de données du système."""
    config = {section: dict(values) for section, values in DEFAULTS.items()}
    config["data"]["folder"] = str(default_data_folder())
    return config


def write_default_config(path: Path, force: bool) -> bool:
    """Écrit config.yaml ; renvoie False s'il existait déjà et que force est faux."""
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(default_config(), allow_unicode=True, sort_keys=False)
    path.write_text(text, encoding="utf-8")
    return True


def load_config() -> Config:
    """Lit config.yaml, le complète avec les valeurs par défaut et le valide."""
    path = config_path()
    if not path.exists():
        raise VeloError(f"configuration introuvable ({path}) : lancez 'velo init'")
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise VeloError(f"config.yaml n'est pas un fichier YAML valide ({exc})") from exc
    if not isinstance(content, dict):
        raise VeloError("config.yaml doit contenir des sections (network, data...)")
    config = default_config()
    for section, values in content.items():
        if section not in config or not isinstance(values, dict):
            raise VeloError(f"config.yaml : section '{section}' inconnue ou vide")
        config[section].update(values)
    validate(config)
    return config


def validate(config: Config) -> None:
    """Vérifie chaque réglage et nomme celui qui est invalide."""
    url = config["network"].get("gbfs_url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise VeloError("config.yaml : network.gbfs_url doit être une URL http(s)")
    if not isinstance(config["network"].get("name"), str):
        raise VeloError("config.yaml : network.name doit être un texte")
    folder = config["data"].get("folder")
    if not isinstance(folder, str) or not folder.strip():
        raise VeloError("config.yaml : data.folder doit être un chemin de dossier")
    for (section, key), minimum in MINIMUMS.items():
        value = config[section].get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            raise VeloError(f"config.yaml : {section}.{key} doit être un entier >= {minimum}")
    if str(config["logging"].get("level")).upper() not in LEVELS:
        raise VeloError(f"config.yaml : logging.level doit valoir {', '.join(LEVELS)}")


def resolve(option: Any, config: Config, section: str, key: str) -> Any:
    """Priorité : option de la commande, puis config.yaml, puis défaut du code."""
    if option is not None:
        return option
    return config.get(section, {}).get(key, DEFAULTS[section][key])


def check_minimum(value: int, minimum: int, name: str) -> int:
    """Renvoie value, ou lève une erreur si elle est sous le minimum autorisé."""
    if value < minimum:
        raise VeloError(f"{name} doit être supérieur ou égal à {minimum}")
    return value


def network_folder(config: Config) -> Path:
    """Dossier des données du réseau : « V'Lille » donne <dossier>/vlille."""
    slug = re.sub(r"[^a-z0-9]+", "", config["network"]["name"].lower())
    return Path(config["data"]["folder"]) / (slug or "reseau")