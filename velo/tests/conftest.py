import copy
import logging

import pytest

from velo import gbfs
from velo.errors import VeloError

GBFS_URL = "https://exemple.test/gbfs.json"

FAKE_API = {
    GBFS_URL: {
        "last_updated": 1763290000,
        "data": {
            "fr": {
                "feeds": [
                    {"name": name, "url": f"https://exemple.test/{name}.json"}
                    for name in (
                        "system_information",
                        "station_information",
                        "station_status",
                        "vehicle_types",
                    )
                ]
            }
        },
    },
    "https://exemple.test/system_information.json": {
        "data": {"name": "V'Lille", "system_id": "vlille"}
    },
    "https://exemple.test/vehicle_types.json": {"data": {"vehicle_types": []}},
    "https://exemple.test/station_information.json": {
        "data": {
            "stations": [
                {"station_id": "42", "name": "Vauban", "lat": 50.6, "lon": 3.0},
                {"station_id": "43", "name": "Gare Lille Flandres", "lat": 50.6, "lon": 3.1},
                {"station_id": "44", "name": "Gare Lille Europe", "lat": 50.6, "lon": 3.1},
                {"station_id": "61", "name": "Solférino", "lat": 50.6, "lon": 3.0},
                {"station_id": "99", "name": "Sans coordonnées"},
            ]
        }
    },
    "https://exemple.test/station_status.json": {
        "last_updated": 1763290000,
        "data": {
            "stations": [
                {
                    "station_id": sid,
                    "num_bikes_available": bikes,
                    "num_docks_available": docks,
                    "is_installed": True,
                    "is_renting": renting,
                    "is_returning": True,
                    "last_reported": 1763289950,
                }
                for sid, bikes, docks, renting in (
                    ("42", 3, 17, True),
                    ("43", 0, 40, True),
                    ("44", 20, 0, True),
                    ("61", 5, 5, False),
                )
            ]
            + [{"station_id": "77", "num_docks_available": 3}]
        },
    },
}


@pytest.fixture(autouse=True)
def restore_logging():
    root = logging.getLogger()
    handlers = list(root.handlers)
    yield
    for handler in root.handlers:
        if handler not in handlers:
            handler.close()
    root.handlers[:] = handlers


@pytest.fixture
def fake_api(monkeypatch):
    api = copy.deepcopy(FAKE_API)

    def fake_fetch(url):
        if url not in api:
            raise VeloError(f"réseau indisponible : {url}")
        return copy.deepcopy(api[url])

    monkeypatch.setattr(gbfs, "fetch_json", fake_fetch)
    return api


@pytest.fixture
def config(tmp_path, fake_api):
    return {
        "network": {"name": "V'Lille", "gbfs_url": GBFS_URL},
        "data": {"folder": str(tmp_path)},
        "refresh": {"max_age_days": 7},
        "collect": {"interval_seconds": 120},
        "alerts": {"low_bikes": 2, "low_docks": 2},
        "dashboard": {"refresh_seconds": 60},
        "logging": {"level": "INFO"},
    }
