"""Small, hand-made test data (NOT real NYC data) so the tests run without the processed files."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import BAND_LABELS, YEARS  # noqa: E402


def make_toy_tables(seed=0):
    rng = np.random.default_rng(seed)
    areas = [(f"104{i:02d}", "Bronx") for i in range(6)] + [(f"112{i:02d}", "Brooklyn") for i in range(6)]
    panel, crashes, buildings, features = [], [], [], []
    for k, (code, borough) in enumerate(areas):
        lon, lat = -73.95 + 0.02 * k, 40.70 + 0.01 * (k % 3)
        features.append({"type": "Feature", "properties": {"modzcta": code},
                         "geometry": {"type": "Polygon", "coordinates": [[[lon, lat], [lon + 0.02, lat], [lon + 0.02, lat + 0.01],
                                                                          [lon, lat + 0.01], [lon, lat]]]}})
        for year in YEARS:
            nc, pres = int(rng.integers(0, 60)) * (k % 4 != 0), int(rng.integers(0, 40)) * (k % 4 != 0)
            local = int(rng.integers(1, 12))
            repeat, unknown = int(rng.integers(0, local + 1)) // 2, 1 if local > 3 else 0
            row = {"modzcta": code, "year": year, "area_borough": borough, "population_2018": 20000 + 1000 * k,
                   "units_completed": nc + pres, "units_new_construction": nc, "units_preservation": pres,
                   "crashes_local": local, "crashes_all": local + 1, "severe_injuries_local": local, "severe_injuries_all": local + 1,
                   "fatalities_local": int(k % 2), "fatalities_all": int(k % 2), "crashes_local_repeat": repeat,
                   "crashes_local_first": local - repeat - unknown, "crashes_local_repeat_unknown": unknown}
            row.update({c: 0 for c in BAND_LABELS})
            row["units_eli"], row["units_li"] = nc, pres
            panel.append(row)
            for _ in range(local + 1):
                crashes.append({"modzcta": code, "area_borough": borough, "crash_year": year, "crash_hour": int(rng.integers(0, 24)),
                                "weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][int(rng.integers(0, 7))],
                                "is_highway": False, "time_exact_midnight": False})
            if nc + pres:
                buildings.append({"modzcta": code, "area_borough": borough, "construction_type": "New Construction" if nc >= pres else "Preservation",
                                  "completion_year": year, "units_counted": nc + pres, "latitude": lat + 0.005, "longitude": lon + 0.01})
    panel = pd.DataFrame(panel)
    coverage = (panel.groupby(["area_borough", "year"], as_index=False)["crashes_all"].sum()
                .rename(columns={"area_borough": "borough", "crashes_all": "crashes_assigned"}))
    coverage["crashes_all"] = coverage["crashes_assigned"] + 3
    pipeline = pd.DataFrame({"modzcta": [a for a, _ in areas[::2]], "pipeline_buildings": 2, "pipeline_units": 100,
                             "pipeline_units_nc": 60, "pipeline_units_pres": 40})
    return {"panel": panel, "crashes": pd.DataFrame(crashes), "pipeline": pipeline, "coverage": coverage,
            "buildings": pd.DataFrame(buildings), "geojson": {"type": "FeatureCollection", "features": features},
            "meta": {"snapshot_date": "test", "source_mode": "offline-test"}}


@pytest.fixture
def toy_data():
    return make_toy_tables()


@pytest.fixture
def toy_data_dir(tmp_path):
    data = make_toy_tables()
    names = {"panel": "panel_modzcta_year.csv", "crashes": "crashes_for_app.csv", "pipeline": "area_pipeline.csv",
             "coverage": "borough_year_summary.csv", "buildings": "buildings_for_app.csv"}
    for key, name in names.items():
        data[key].to_csv(tmp_path / name, index=False)
    (tmp_path / "modzcta_simplified.geojson").write_text(json.dumps(data["geojson"]))
    (tmp_path / "metadata.json").write_text(json.dumps(data["meta"]))
    return tmp_path
