from datetime import timedelta

import pytest
from conftest import GBFS_URL

from velo.collect import Report, collect_once, format_report, parse_duration
from velo.errors import VeloError


def test_parse_duration():
    assert parse_duration("3h") == timedelta(hours=3)
    assert parse_duration("45m") == timedelta(minutes=45)
    assert parse_duration("1h30m") == timedelta(hours=1, minutes=30)
    for wrong in ("", "3", "h", "2j"):
        with pytest.raises(VeloError):
            parse_duration(wrong)


def test_same_last_updated_is_saved_once(tmp_path, fake_api):
    report = Report()
    previous = collect_once(GBFS_URL, tmp_path, None, report)
    collect_once(GBFS_URL, tmp_path, previous, report)
    assert report.count == 1
    lines = next(tmp_path.glob("*.csv")).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 + 4


def test_new_last_updated_is_saved(tmp_path, fake_api):
    report = Report()
    previous = collect_once(GBFS_URL, tmp_path, None, report)
    fake_api["https://exemple.test/station_status.json"]["last_updated"] += 120
    collect_once(GBFS_URL, tmp_path, previous, report)
    assert report.count == 2
    assert "2 relevé(s)" in format_report(report)


def test_report_without_snapshot():
    assert format_report(Report()) == "Bilan : aucun relevé enregistré."