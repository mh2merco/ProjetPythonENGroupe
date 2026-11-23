from conftest import GBFS_URL

from velo.gbfs import (
    discover_feeds,
    download_rare_feeds,
    fetch_snapshot,
    load_network_name,
    load_stations,
    parse_time,
)


def test_discover_feeds_gbfs_2(fake_api):
    feeds = discover_feeds(GBFS_URL)
    assert feeds["station_status"] == "https://exemple.test/station_status.json"


def test_discover_feeds_gbfs_3(fake_api):
    fake_api[GBFS_URL]["data"] = fake_api[GBFS_URL]["data"]["fr"]
    assert "station_information" in discover_feeds(GBFS_URL)


def test_parse_time_accepts_both_formats():
    a = parse_time(1763290000)
    b = parse_time("2025-11-16T10:46:40+00:00")
    assert a == b
    assert a.tzinfo is not None


def test_download_and_load(tmp_path, fake_api):
    count = download_rare_feeds(GBFS_URL, tmp_path)
    assert count == 4
    assert (tmp_path / "vehicle_types.json").exists()
    assert load_network_name(tmp_path) == "V'Lille"
    assert load_stations(tmp_path)["43"].name == "Gare Lille Flandres"


def test_invalid_status_is_ignored(fake_api):
    snapshot = fetch_snapshot(GBFS_URL)
    assert [s.station_id for s in snapshot.statuses] == ["42", "43", "44", "61"]
    assert snapshot.statuses[0].bikes == 3
