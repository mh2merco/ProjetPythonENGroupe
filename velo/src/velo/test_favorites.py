import pytest

from velo.errors import VeloError
from velo.favorites import (
    MAX_FAVORITES,
    add_favorite,
    favorite_rows,
    load_favorites,
    remove_favorite,
)
from velo.gbfs import download_rare_feeds, fetch_snapshot, load_stations

STATIONS = {str(i): None for i in range(1, 20)}


def test_add_and_remove(tmp_path):
    assert load_favorites(tmp_path) == []
    add_favorite(tmp_path, "3", STATIONS)
    add_favorite(tmp_path, "1", STATIONS)
    assert load_favorites(tmp_path) == ["3", "1"]
    remove_favorite(tmp_path, "3")
    assert load_favorites(tmp_path) == ["1"]


def test_add_errors(tmp_path):
    add_favorite(tmp_path, "1", STATIONS)
    with pytest.raises(VeloError, match="inconnue"):
        add_favorite(tmp_path, "999", STATIONS)
    with pytest.raises(VeloError, match="déjà"):
        add_favorite(tmp_path, "1", STATIONS)


def test_maximum_is_ten(tmp_path):
    for i in range(1, MAX_FAVORITES + 1):
        add_favorite(tmp_path, str(i), STATIONS)
    with pytest.raises(VeloError, match="maximum"):
        add_favorite(tmp_path, "15", STATIONS)


def test_remove_unknown_favorite(tmp_path):
    with pytest.raises(VeloError, match="n'est pas"):
        remove_favorite(tmp_path, "4")


def test_rows_show_state(tmp_path, config):
    url = config["network"]["gbfs_url"]
    download_rare_feeds(url, tmp_path)
    rows = favorite_rows(["42", "43"], load_stations(tmp_path), fetch_snapshot(url), 2, 2)
    assert rows == [["42", "Vauban", 3, 17, ""], ["43", "Gare Lille Flandres", 0, 40, "vide"]]git add .
