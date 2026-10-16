"""Known-answer tests for the shared calculations (the same checks run in notebook Section 10.2)."""
import numpy as np
import pandas as pd

from src.analysis import (DEFAULT_FILTERS, YEARS, add_production_tier, build_report, compute_area_metrics, lookback_shares,
                          merge_filters, parse_search, priority_ranking, spearman)


def hand_panel():
    spec = {"A": ("Manhattan", 10000, 10, 10, 2), "B": ("Manhattan", 20000, 0, 0, 1),
            "C": ("Brooklyn", 40000, 4, 0, 4), "D": ("Brooklyn", 5000, 10, 6, 1)}
    rows = []
    for code, (borough, pop, units, nc, crashes) in spec.items():
        for year in YEARS:
            rows.append({"modzcta": code, "year": year, "area_borough": borough, "population_2018": pop, "units_completed": units,
                         "units_new_construction": nc, "units_preservation": units - nc, "units_eli": units, "units_vli": 0,
                         "units_li": 0, "units_mod": 0, "units_mid": 0, "units_other_income": 0, "crashes_local": crashes,
                         "crashes_all": crashes + 1, "severe_injuries_local": crashes, "severe_injuries_all": crashes + 1,
                         "fatalities_local": 0, "fatalities_all": 0, "crashes_local_repeat": 0, "crashes_local_first": crashes,
                         "crashes_local_repeat_unknown": 0})
    return pd.DataFrame(rows)


def test_rates_are_per_resident_and_per_year():
    a = compute_area_metrics(hand_panel()).set_index("modzcta")
    assert np.isclose(a.loc["A", "units_per_1k"], 4.0)          # 40 units / 10,000 residents * 1,000
    assert np.isclose(a.loc["A", "crash_rate"], 20.0)           # 8 crashes / 4 years / 10,000 * 100,000
    one_year = compute_area_metrics(hand_panel(), years=[2022]).set_index("modzcta")
    assert np.isclose(one_year.loc["A", "units_per_1k"], 1.0) and np.isclose(one_year.loc["A", "crash_rate"], 20.0)


def test_tiers_and_totals_preserved():
    p = hand_panel()
    a = add_production_tier(compute_area_metrics(p)).set_index("modzcta")
    assert a["production_tier"].to_dict() == {"A": "Lower half", "B": "No completions", "C": "Lower half", "D": "Upper half"}
    assert a["units"].sum() == p["units_completed"].sum() and a["crash_total"].sum() == p["crashes_local"].sum()


def test_lookback_unknown_is_not_counted_as_none():
    lb = lookback_shares(pd.DataFrame({"production_tier": ["Upper half", "Upper half"], "crashes_local_repeat": [1, 0],
                                       "crashes_local_first": [1, 1], "crashes_local_repeat_unknown": [5, 0]}))
    assert np.isclose(lb.loc["Upper half", "share_known_pct"], 100 / 3)


def test_priority_score_is_average_of_percentiles():
    area = compute_area_metrics(hand_panel())
    top = priority_ranking(area, pd.DataFrame({"modzcta": ["A", "C"], "pipeline_buildings": [1, 2], "pipeline_units": [50, 50],
                                               "pipeline_units_nc": [50, 0], "pipeline_units_pres": [0, 50]}))
    assert list(top["modzcta"]) == ["A", "C"]
    assert np.allclose(top["priority_score"], (top["pipeline_pct"] + top["crash_pct"]) / 2)


def test_spearman_needs_enough_areas():
    assert np.isnan(spearman(pd.Series(range(5)), pd.Series(range(5)))[0])
    rho, n = spearman(pd.Series(range(20)), pd.Series(range(20)) ** 2)
    assert np.isclose(rho, 1.0) and n == 20


def test_search_examples():
    assert parse_search("Brooklyn 2023 new construction")["filters"] == {"years": [2023], "boroughs": ["Brooklyn"],
                                                                         "housing_type": "New Construction"}
    assert parse_search("Brooklyn 2022 new buildings")["filters"]["housing_type"] == "New Construction"
    p = parse_search("Bronx fatalities 2022-2024 highways")["filters"]
    assert p == {"years": [2022, 2023, 2024], "boroughs": ["Bronx"], "crash_measure": "fatalities", "crash_scope": "all"}
    p = parse_search("Queens 2026 preservation")
    assert "2026" in p["ignored"] and "years" not in p["filters"]          # partial year is reported, not used
    assert parse_search("hello")["filters"] == {}


def test_merge_filters_search_overrides_dropdowns_and_empty_falls_back():
    f = merge_filters({"boroughs": ["Queens"], "years": [2024], "housing_type": "All", "crash_measure": "crashes",
                       "crash_scope": "local"}, parse_search("Brooklyn"))
    assert f["boroughs"] == ["Brooklyn"] and f["years"] == [2024]
    f = merge_filters({"boroughs": [], "years": None}, {"filters": {}})
    assert f["boroughs"] == DEFAULT_FILTERS["boroughs"] and f["years"] == YEARS


def test_report_for_default_and_small_selection(toy_data):
    report = build_report(toy_data, DEFAULT_FILTERS)
    assert not report["empty"] and report["kpis"]["areas"] == 12
    assert np.isclose(report["kpis"]["units"], toy_data["panel"]["units_completed"].sum())
    small = build_report(toy_data, {**DEFAULT_FILTERS, "boroughs": ["Bronx"], "years": [2022]})
    assert small["kpis"]["areas"] == 6 and np.isnan(small["rho"])           # too few areas: no correlation is reported


def test_coverage_includes_unknown_borough_only_citywide():
    from src.analysis import BOROUGHS, coverage_by_year
    cov = pd.DataFrame({"borough": ["Bronx", "Queens", "Unknown"], "year": [2025, 2025, 2025],
                        "crashes_all": [10, 20, 2], "crashes_assigned": [8, 18, 0]})
    citywide = coverage_by_year(cov, [2025], BOROUGHS)
    assert int(citywide["crashes_all"].iloc[0]) == 32 and int(citywide["crashes_assigned"].iloc[0]) == 26
    queens = coverage_by_year(cov, [2025], ["Queens"])
    assert int(queens["crashes_all"].iloc[0]) == 20
