import pytest
import am_settings, sessions


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(sessions, "DATA_DIR", str(tmp_path))


def test_defaults_come_from_the_sample_report():
    s = am_settings.load()
    assert s["submitter"] == "Nguyen" and s["reviewer"] == "Jonas (COO)"
    assert "Le Minh Tri" in s["dev_roster"] and "Thang Dam Quyet" in s["seo_roster"]


def test_save_round_trips_and_cleans():
    saved = am_settings.save({"submitter": "  Mimi  ", "reviewer": "Jonas", "dev_roster": ["A", " A ", "", "B"], "seo_roster": []})
    assert saved["submitter"] == "Mimi" and saved["dev_roster"] == ["A", "B"] and saved["seo_roster"] == []
    assert am_settings.load() == saved


@pytest.mark.parametrize("bad", [
    {"submitter": "", "reviewer": "J", "dev_roster": [], "seo_roster": []},
    {"submitter": "x" * 200, "reviewer": "J", "dev_roster": [], "seo_roster": []},
    {"submitter": "N", "reviewer": "J", "dev_roster": "A,B", "seo_roster": []},
    {"submitter": "N", "reviewer": "J", "dev_roster": [1], "seo_roster": []},
    {"submitter": "N", "reviewer": "J", "dev_roster": [f"n{i}" for i in range(50)], "seo_roster": []},
])
def test_save_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        am_settings.save(bad)


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    (tmp_path / "am_settings.json").write_text("{nope")
    assert am_settings.load()["submitter"] == "Nguyen"
