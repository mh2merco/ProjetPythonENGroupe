from velo.config import network_folder
from velo.gbfs import download_rare_feeds
from velo.status import format_summary, load_current, summarize


def test_summary_counts(config):
    download_rare_feeds(config["network"]["gbfs_url"], network_folder(config))
    name, snapshot, stations = load_current(config)
    summary = summarize(name, snapshot, stations)
    assert summary.total == 4
    assert summary.in_service == 3
    assert summary.out_of_service == 1
    assert (summary.empty, summary.full) == (1, 1)
    assert (summary.bikes, summary.docks) == (23, 57)
    assert "taux de remplissage 29 %" in format_summary(summary)
