import csv
from datetime import datetime, timedelta

from velo.models import Snapshot, StationStatus
from velo.storage import COLUMNS, append_snapshot, last_timestamp

TZ = datetime.now().astimezone().tzinfo


def snapshot_at(moment):
    status = StationStatus("42", 3, 17, True, True, False, moment - timedelta(seconds=19))
    return Snapshot(moment, [status])


def test_one_file_per_day_with_header(tmp_path):
    first = datetime(2026, 11, 18, 8, 14, tzinfo=TZ)
    append_snapshot(tmp_path, snapshot_at(first))
    path = append_snapshot(tmp_path, snapshot_at(first + timedelta(minutes=2)))
    assert path.name == "2026-11-18.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == COLUMNS
    assert len(rows) == 3
    assert rows[1][0] == first.isoformat()
    assert rows[1][4:7] == ["true", "true", "false"]


def test_collect_after_midnight_goes_to_next_file(tmp_path):
    append_snapshot(tmp_path, snapshot_at(datetime(2026, 11, 18, 23, 59, tzinfo=TZ)))
    append_snapshot(tmp_path, snapshot_at(datetime(2026, 11, 19, 0, 1, tzinfo=TZ)))
    names = sorted(p.name for p in tmp_path.glob("*.csv"))
    assert names == ["2026-11-18.csv", "2026-11-19.csv"]


def test_last_timestamp(tmp_path):
    assert last_timestamp(tmp_path) is None
    moment = datetime(2026, 11, 18, 8, 14, tzinfo=TZ)
    append_snapshot(tmp_path, snapshot_at(moment))
    assert last_timestamp(tmp_path) == moment