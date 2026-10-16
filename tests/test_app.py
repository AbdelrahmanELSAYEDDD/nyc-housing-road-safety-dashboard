"""The website starts, the Generate Report callback applies dropdowns and search, and empty selections are handled."""
import importlib
import json
import sys

import pytest


@pytest.fixture
def app_module(toy_data_dir, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(toy_data_dir))
    sys.modules.pop("app", None)
    return importlib.import_module("app")


def call(app_module, boroughs=None, years=None, housing="All", measure="crashes", scope="local", query=""):
    return app_module.generate_report(1, None, boroughs if boroughs is not None else ["Bronx", "Brooklyn"],
                                      years if years is not None else [2022, 2023, 2024, 2025], housing, measure, scope, query)


def test_pages_load(app_module):
    client = app_module.server.test_client()
    assert client.get("/").status_code == 200
    layout = client.get("/_dash-layout")
    assert layout.status_code == 200
    text = layout.get_data(as_text=True)
    assert "Generate Report" in text and "Data story" in text and "What surprised us" in text and "Test data" in text


def test_generate_report_returns_eight_figures(app_module):
    out = call(app_module)
    figures = out[-8:]
    assert len(figures) == 8
    titles = [json.loads(f.to_json())["layout"]["title"]["text"] for f in figures]
    assert all(f"RQ{i}" in t for i, t in enumerate(titles, start=1))


def test_search_sets_dropdowns_and_clears_box(app_module):
    out = call(app_module, query="Brooklyn 2023 new construction fatalities")
    boroughs, years, housing, measure, scope, search_box, feedback = out[:7]
    assert boroughs == ["Brooklyn"] and years == [2023] and housing == "New Construction" and measure == "fatalities"
    assert search_box == "" and "Search applied" in feedback


def test_dropdowns_change_the_report(app_module):
    all_kpis = call(app_module)[8]
    bronx_kpis = call(app_module, boroughs=["Bronx"])[8]
    assert str(all_kpis) != str(bronx_kpis)


def test_empty_and_unknown_inputs_are_explained(app_module):
    out = call(app_module, boroughs=[], years=[], query="hello 2026")
    assert out[0] == ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"] and out[1] == [2022, 2023, 2024, 2025]  # fall back to all
    feedback = out[6]
    assert "No borough was selected" in feedback and "No year was selected" in feedback
    assert "“2026”" in feedback and "No filter words were recognised" in feedback


def test_missing_data_shows_instructions(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    sys.modules.pop("app", None)
    app_module = importlib.import_module("app")
    text = app_module.server.test_client().get("/_dash-layout").get_data(as_text=True)
    assert "Processed data files are missing" in text and "panel_modzcta_year.csv" in text
