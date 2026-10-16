"""Calculations for the eight research questions, used by both the notebook and the Dash website.

Keeping them in one file means the notebook and the website always give the same numbers.
The functions take tables and return tables; only load_app_data reads files.

The tables come from the files the notebook saves in data/processed/:
  panel     -- one row per ZIP area (MODZCTA) and year, 2022-2025 (panel_modzcta_year.csv)
  crashes   -- one row per serious crash placed in a ZIP area, 2022-2025 (crashes_for_app.csv)
  pipeline  -- one row per ZIP area with unfinished affordable units (area_pipeline.csv)
  coverage  -- per borough and year: all crashes and crashes placed in an area (borough_year_summary.csv)
  buildings -- completed buildings 2022-2025 with coordinates, for the RQ2 map (buildings_for_app.csv)
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = [2022, 2023, 2024, 2025]
BOROUGHS = ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]
HOUSING_TYPES = {"All": "units_completed", "New Construction": "units_new_construction", "Preservation": "units_preservation"}
PIPELINE_COLUMNS = {"All": "pipeline_units", "New Construction": "pipeline_units_nc", "Preservation": "pipeline_units_pres"}
CRASH_MEASURES = {"crashes": "Serious crashes", "severe_injuries": "Severe injuries", "fatalities": "Fatalities"}
CRASH_SCOPES = {"local": "Local streets", "all": "All roads (incl. highways)"}
TIER_ORDER = ["No completions", "Lower half", "Upper half"]
QUADRANTS = ["High production · high crash rate", "High production · lower crash rate",
             "Lower/no production · high crash rate", "Lower/no production · lower crash rate"]
TYPE_ORDER = ["New-construction dominant", "Mixed", "Preservation dominant", "No completions"]
BAND_LABELS = {"units_eli": "Extremely low income", "units_vli": "Very low income", "units_li": "Low income",
               "units_mod": "Moderate income", "units_mid": "Middle income", "units_other_income": "Other income units"}
BLOCKS = ["00–03", "03–06", "06–09", "09–12", "12–15", "15–18", "18–21", "21–24"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MIN_AREAS_FOR_CORRELATION = 10
DEFAULT_FILTERS = {"boroughs": list(BOROUGHS), "years": list(YEARS), "housing_type": "All",
                   "crash_measure": "crashes", "crash_scope": "local"}


def as_bool(values):
    """Turn a True/False column that may contain missing values into plain True/False (missing counts as False)."""
    return pd.Series(values).fillna(False).to_numpy(dtype=bool)


# Area numbers used by every research question

def compute_area_metrics(panel, years=YEARS, boroughs=None, housing_type="All", crash_measure="crashes", crash_scope="local"):
    """One row per ZIP area for the selected filters.

    units_per_1k = affordable units completed in the selected years per 1,000 residents (2018 population)
    crash_rate   = crashes (or injuries / deaths) per 100,000 residents per year:
                   the total is divided by the number of selected years, so one year and four years are comparable
    """
    years = sorted(int(y) for y in years)
    if not years or not set(years) <= set(YEARS):
        raise ValueError(f"years must be a non-empty subset of {YEARS}")
    if housing_type not in HOUSING_TYPES or crash_measure not in CRASH_MEASURES or crash_scope not in CRASH_SCOPES:
        raise ValueError("unknown housing_type, crash_measure or crash_scope")
    p = panel[panel["year"].isin(years)]
    if boroughs:
        p = p[p["area_borough"].isin(boroughs)]
    crash_col = f"{crash_measure}_{crash_scope}"
    sums = ["units_completed", "units_new_construction", "units_preservation", *BAND_LABELS, "crashes_local", "crashes_all",
            "fatalities_local", "crashes_local_repeat", "crashes_local_first", "crashes_local_repeat_unknown"]
    area = (p.assign(units=p[HOUSING_TYPES[housing_type]].astype(float), crash_total=p[crash_col].astype(float))
              .groupby("modzcta", as_index=False)
              .agg(area_borough=("area_borough", "first"), population_2018=("population_2018", "first"),
                   units=("units", "sum"), crash_total=("crash_total", "sum"), **{c: (c, "sum") for c in sums}))
    population = area["population_2018"].astype(float)
    area["n_years"] = len(years)
    area["units_per_1k"] = 1000 * area["units"] / population
    area["crash_rate"] = 100000 * area["crash_total"] / len(years) / population
    return area


def spearman(x, y, min_n=MIN_AREAS_FOR_CORRELATION):
    """Spearman rank correlation and the number of areas used. With fewer than 10 areas we return NaN instead of a number."""
    d = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(d) < min_n or d["x"].nunique() < 2 or d["y"].nunique() < 2:
        return np.nan, len(d)
    return float(d["x"].rank().corr(d["y"].rank())), len(d)


def describe_strength(rho):
    """Describe a correlation in words (negligible, weak, moderate or strong). It never says anything about cause."""
    if pd.isna(rho):
        return "not enough areas to measure"
    size = abs(rho)
    strength = "negligible" if size < 0.1 else "weak" if size < 0.3 else "moderate" if size < 0.5 else "strong"
    return f"{strength} {'positive' if rho > 0 else 'negative'} association"


def add_production_tier(area):
    """Put each area in a production tier: No completions (0 units), or the lower or upper half of the areas
    that did complete units (split at their median units per 1,000 residents)."""
    a = area.copy()
    has = a["units"].gt(0) & a["units_per_1k"].notna()
    median = a.loc[has, "units_per_1k"].median()
    tier = np.select([as_bool(a["units"].eq(0)), as_bool(has & a["units_per_1k"].gt(median)), as_bool(has)],
                     ["No completions", "Upper half", "Lower half"], default="")
    a["production_tier"] = pd.Series(tier, index=a.index).replace("", np.nan)
    a.loc[a["population_2018"].isna(), "production_tier"] = np.nan
    a.attrs["tier_median"] = float(median) if pd.notna(median) else np.nan
    return a


def classify_quadrants(area):
    """RQ2: combine the production tier (upper half = high) with the crash rate (at or above the median = high)."""
    crash_median = area["crash_rate"].median()
    high_prod = as_bool(area["production_tier"].eq("Upper half"))
    high_crash = as_bool(area["crash_rate"] >= crash_median)
    quadrant = np.select([high_prod & high_crash, high_prod, high_crash], QUADRANTS[:3], default=QUADRANTS[3])
    return pd.Series(quadrant, index=area.index).where(area["crash_rate"].notna()), float(crash_median)


def indexed_trend(panel, tier_by_area, crash_col):
    """RQ3: crashes per tier and year, shown as an index where the first selected year = 100."""
    p = panel.assign(tier=panel["modzcta"].map(tier_by_area)).dropna(subset=["tier"])
    trend = p.groupby(["tier", "year"], as_index=False).agg(value=(crash_col, "sum"), areas=("modzcta", "nunique"))
    trend["value"] = trend["value"].astype(float)
    base = trend[trend["year"] == trend["year"].min()].set_index("tier")["value"]
    trend["index"] = 100 * trend["value"] / trend["tier"].map(base).replace(0, np.nan)
    return trend


def time_block_shares(crashes, upper_areas):
    """RQ4: for upper-half areas and for all other areas, the share of crashes in each weekday x 3-hour cell
    (each group adds up to 100%), and the difference between the two groups in percentage points."""
    c = crashes.copy()
    c["group"] = np.where(c["modzcta"].isin(upper_areas), "upper", "other")
    c["time_block"] = np.array(BLOCKS)[(c["crash_hour"].astype(int) // 3).to_numpy()]     # hour 0-2 -> "00–03", 3-5 -> "03–06", ...
    counts = (c.groupby(["group", "time_block", "weekday"]).size().unstack("group")
                .reindex(pd.MultiIndex.from_product([BLOCKS, DAYS], names=["time_block", "weekday"]))
                .reindex(columns=["upper", "other"]).fillna(0))
    n_upper, n_other = counts["upper"].sum(), counts["other"].sum()
    cells = counts.reset_index().rename(columns={"upper": "count_upper", "other": "count_other"})
    cells["share_upper_pct"] = 100 * cells["count_upper"] / n_upper if n_upper else np.nan
    cells["share_other_pct"] = 100 * cells["count_other"] / n_other if n_other else np.nan
    cells["diff_pp"] = cells["share_upper_pct"] - cells["share_other_pct"]
    cells.attrs.update({"n_upper": int(n_upper), "n_other": int(n_other)})
    return cells


def classify_dominant_type(area, nc_high=0.6, nc_low=0.4):
    """RQ5: new-construction dominant if more than 60% of the completed units are new construction,
    preservation dominant if less than 40%, otherwise mixed."""
    total = area["units_new_construction"].astype(float) + area["units_preservation"].astype(float)
    nc_share = area["units_new_construction"].astype(float) / total.where(total > 0)
    kind = np.select([as_bool(total.eq(0)), as_bool(nc_share > nc_high), as_bool(nc_share < nc_low)],
                     ["No completions", "New-construction dominant", "Preservation dominant"], default="Mixed")
    return pd.Series(kind, index=area.index), nc_share


def type_summary(area):
    """RQ5 table: number of areas, median crash rate and the middle 50% range for each group."""
    d = area.dropna(subset=["crash_rate"])
    s = d.groupby("dominant_type").agg(areas=("modzcta", "size"), median_crash_rate=("crash_rate", "median"),
                                       q1=("crash_rate", lambda v: v.quantile(0.25)), q3=("crash_rate", lambda v: v.quantile(0.75)),
                                       units=("units", "sum"))
    return s.reindex(TYPE_ORDER)


def weighted_band_rates(area):
    """RQ6: for each income band, the crash rate of the area where its average unit was completed
    (each area's rate weighted by the band's units there). For comparison, the rate of the average resident
    (each area's rate weighted by its population)."""
    v = area.dropna(subset=["crash_rate", "population_2018"])
    rows = []
    for col, label in BAND_LABELS.items():
        units = v[col].astype(float)
        rate = (units * v["crash_rate"]).sum() / units.sum() if units.sum() > 0 else np.nan   # weighted average
        rows.append({"band": label, "units": int(units.sum()), "weighted_crash_rate": rate})
    pop = v["population_2018"].astype(float)
    resident_avg = float((pop * v["crash_rate"]).sum() / pop.sum()) if pop.sum() > 0 else np.nan
    return pd.DataFrame(rows), resident_avg


def lookback_shares(area):
    """RQ7: per production tier, count crashes with an earlier similar serious injury recorded, with none recorded,
    and with a blank (unknown) value. The share only uses the known values; a blank is never counted as "none"."""
    s = (area.dropna(subset=["production_tier"]).groupby("production_tier")
             [["crashes_local_repeat", "crashes_local_first", "crashes_local_repeat_unknown"]].sum().astype(int))
    s.columns = ["earlier_recorded", "none_recorded", "unknown"]
    known = s["earlier_recorded"] + s["none_recorded"]
    s["share_known_pct"] = 100 * s["earlier_recorded"] / known.where(known > 0)
    return s.reindex(TIER_ORDER)


def priority_ranking(area, pipeline, housing_type="All", top_n=15):
    """RQ8: rank the areas by unfinished units per resident and by crash rate (as percentiles); the score is the
    average of the two. A higher score puts the area higher on the list. It is a list of places to look at more
    closely, not a prediction. Equal scores share a rank and are ordered by the crash percentile."""
    col = PIPELINE_COLUMNS[housing_type]
    a = area.merge(pipeline[["modzcta", "pipeline_buildings", "pipeline_units", "pipeline_units_nc", "pipeline_units_pres"]],
                   on="modzcta", how="left", validate="one_to_one")
    for c in ["pipeline_buildings", "pipeline_units", "pipeline_units_nc", "pipeline_units_pres"]:
        a[c] = a[c].fillna(0)
    a["pipeline_selected"] = a[col].astype(float)
    a["pipeline_per_1k"] = 1000 * a["pipeline_selected"] / a["population_2018"].astype(float)
    # Percentile ranks (0-100) among the areas that have both values.
    valid = a["pipeline_per_1k"].notna() & a["crash_rate"].notna()
    a["pipeline_pct"] = a.loc[valid, "pipeline_per_1k"].rank(pct=True) * 100
    a["crash_pct"] = a.loc[valid, "crash_rate"].rank(pct=True) * 100
    a["priority_score"] = (a["pipeline_pct"] + a["crash_pct"]) / 2
    a["nc_pipeline_share"] = a["pipeline_units_nc"] / a["pipeline_units"].where(a["pipeline_units"] > 0)
    # Only areas with unfinished units can be on the list. Ties are sorted in a fixed order, so the list is always the same.
    top = a[valid & a["pipeline_selected"].gt(0)].sort_values(
        ["priority_score", "crash_pct", "pipeline_pct", "modzcta"], ascending=[False, False, False, True]).head(top_n).copy()
    top["priority_rank"] = top["priority_score"].rank(method="min", ascending=False).astype(int)
    return top


# Website search (simple keyword rules) and the full report

BOROUGH_WORDS = {"bronx": "Bronx", "bx": "Bronx", "brooklyn": "Brooklyn", "bk": "Brooklyn", "bklyn": "Brooklyn",
                 "manhattan": "Manhattan", "mn": "Manhattan", "queens": "Queens", "qns": "Queens",
                 "staten island": "Staten Island", "staten": "Staten Island", "si": "Staten Island"}
HOUSING_WORDS = {"new construction": "New Construction", "new-construction": "New Construction", "new buildings": "New Construction",
                 "new building": "New Construction", "new build": "New Construction", "new builds": "New Construction",
                 "newly built": "New Construction", "new homes": "New Construction", "preservation": "Preservation",
                 "preserved": "Preservation", "rehabilitation": "Preservation", "rehab": "Preservation",
                 "all housing": "All", "all construction": "All", "all types": "All"}
MEASURE_WORDS = {"fatalities": "fatalities", "fatality": "fatalities", "fatal": "fatalities", "deaths": "fatalities", "killed": "fatalities",
                 "severe injuries": "severe_injuries", "severe": "severe_injuries", "injuries": "severe_injuries",
                 "crashes": "crashes", "crash": "crashes", "collisions": "crashes"}
SCOPE_WORDS = {"including highways": "all", "incl highways": "all", "all roads": "all", "highways": "all", "highway": "all",
               "local streets": "local", "local": "local"}
STOP_WORDS = {"in", "and", "the", "of", "for", "show", "me", "with", "units", "unit", "housing", "affordable", "nyc", "year", "years",
              "data", "on", "to", "from", "report", "areas", "area", "&", ","}


def parse_search(text):
    """Turn a search such as 'Brooklyn 2023 new construction fatal' into filter values.

    Returns {'filters': {...only the filters that were mentioned...}, 'recognized': [...], 'ignored': [...]}.
    Longer phrases are matched first. Years 2022-2025 and ranges such as 2022-2024 are recognised;
    other years (for example 2026, which is not complete) are listed as ignored instead of being used.
    """
    remaining = f" {str(text or '').lower()} "
    filters, recognized = {}, []

    def take(phrases, key, multi=False):
        # Look for each phrase as a whole word; when found, save the filter value and remove the phrase from the text.
        nonlocal remaining
        for phrase in sorted(phrases, key=len, reverse=True):
            pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
            if re.search(pattern, remaining):
                value = phrases[phrase]
                if multi:
                    filters.setdefault(key, [])
                    if value not in filters[key]:
                        filters[key].append(value)
                elif key not in filters:
                    filters[key] = value
                recognized.append(phrase)
                remaining = re.sub(pattern, " ", remaining)

    # Years: first ranges such as "2022-2024", then single years.
    for a, b in re.findall(r"(20\d\d)\s*[-–to]+\s*(20\d\d)", remaining):
        span = [y for y in range(int(a), int(b) + 1) if y in YEARS]
        if span:
            filters["years"] = sorted(set(filters.get("years", []) + span))
            recognized.append(f"{a}-{b}")
    remaining = re.sub(r"(20\d\d)\s*[-–to]+\s*(20\d\d)", " ", remaining)
    outside_window = []
    for y in re.findall(r"(?<!\d)(20\d\d)(?!\d)", remaining):
        if int(y) in YEARS:
            filters["years"] = sorted(set(filters.get("years", []) + [int(y)]))
            recognized.append(y)
        else:
            outside_window.append(y)          # e.g. 2026: shown back to the user, not used
        remaining = re.sub(rf"(?<!\d){y}(?!\d)", " ", remaining)
    if re.search(r"(?<![a-z])all years(?![a-z])", remaining):
        filters["years"] = list(YEARS)
        recognized.append("all years")
        remaining = re.sub(r"all years", " ", remaining)
    # Then the keyword lists: boroughs, construction type, crash measure and road type.
    take(BOROUGH_WORDS, "boroughs", multi=True)
    take(HOUSING_WORDS, "housing_type")
    take(MEASURE_WORDS, "crash_measure")
    take(SCOPE_WORDS, "crash_scope")
    if re.search(r"(?<![a-z])(citywide|all boroughs)(?![a-z])", remaining):
        filters["boroughs"] = list(BOROUGHS)
        recognized.append("citywide")
        remaining = re.sub(r"(citywide|all boroughs)", " ", remaining)
    # Anything left (except small words such as "in" or "and") is reported back as not recognised.
    ignored = outside_window + [w for w in re.findall(r"[a-z0-9\-]+", remaining) if w not in STOP_WORDS]
    return {"filters": filters, "recognized": recognized, "ignored": ignored}


def merge_filters(dropdowns, parsed):
    """Words from the search replace the matching dropdown values; all other dropdowns stay as they are.
    An empty dropdown falls back to all boroughs or all years."""
    merged = {**DEFAULT_FILTERS, **{k: v for k, v in dropdowns.items() if v}}
    merged.update(parsed.get("filters", {}))
    merged["boroughs"] = [b for b in BOROUGHS if b in (merged.get("boroughs") or BOROUGHS)]
    merged["years"] = sorted(int(y) for y in (merged.get("years") or YEARS))
    return merged


def coverage_by_year(coverage, years, boroughs):
    """Share of crashes that could be placed in a ZIP area, per year, for the selected boroughs.
    Crashes with an unknown borough only belong to the citywide view, so they are included
    only when all five boroughs are selected."""
    selected = list(boroughs) + (["Unknown"] if set(BOROUGHS) <= set(boroughs) else [])
    c = coverage[coverage["year"].isin(years) & coverage["borough"].isin(selected)]
    out = c.groupby("year", as_index=False)[["crashes_all", "crashes_assigned"]].sum()
    out["assignment_rate_pct"] = 100 * out["crashes_assigned"] / out["crashes_all"].where(out["crashes_all"] > 0)
    return out


def select_buildings(buildings, filters):
    """Completed buildings for the RQ2 map that match the selected years, boroughs and construction type."""
    b = buildings[buildings["completion_year"].astype(int).isin(filters["years"]) & buildings["area_borough"].isin(filters["boroughs"])]
    if filters["housing_type"] != "All":
        b = b[b["construction_type"].eq(filters["housing_type"])]
    return b


def build_report(data, filters):
    """Calculate everything the website shows for one set of filters (the notebook uses the default filters).
    Returns a dictionary of tables; "empty" is True when no area matches."""
    f = merge_filters(filters, {})
    area = compute_area_metrics(data["panel"], f["years"], f["boroughs"], f["housing_type"], f["crash_measure"], f["crash_scope"])
    report = {"filters": f, "area": area, "empty": area.empty or area["population_2018"].notna().sum() == 0}
    if report["empty"]:
        return report
    area = add_production_tier(area)
    area["quadrant"], report["crash_median"] = classify_quadrants(area)
    area["dominant_type"], area["nc_share"] = classify_dominant_type(area)
    tier_by_area = area.set_index("modzcta")["production_tier"]
    panel_sel = data["panel"][data["panel"]["year"].isin(f["years"]) & data["panel"]["area_borough"].isin(f["boroughs"])]
    crash_col = f"{f['crash_measure']}_{f['crash_scope']}"
    report["trend"] = indexed_trend(panel_sel, tier_by_area, crash_col)
    report["coverage"] = coverage_by_year(data["coverage"], f["years"], f["boroughs"])
    # RQ4 uses crashes with a known time; 00:00 is left out because it usually means "time unknown".
    cr = data["crashes"]
    cr = cr[cr["crash_year"].isin(f["years"]) & cr["area_borough"].isin(f["boroughs"]) & cr["crash_hour"].notna()
            & ~cr["time_exact_midnight"].astype(bool)]
    if f["crash_scope"] == "local":
        cr = cr[~cr["is_highway"].astype(bool)]
    upper = set(area.loc[area["production_tier"].eq("Upper half"), "modzcta"])
    report["time_cells"] = time_block_shares(cr, upper) if len(cr) else None
    report["types"] = type_summary(area)
    report["bands"], report["resident_avg"] = weighted_band_rates(area)
    report["lookback"] = lookback_shares(area)
    report["priority"] = priority_ranking(area, data["pipeline"], f["housing_type"])
    report["buildings"] = select_buildings(data["buildings"], f) if "buildings" in data else None
    rho, n = spearman(area["units_per_1k"], area["crash_rate"])
    report.update({"area": area, "rho": rho, "n_corr": n})
    report["kpis"] = {"areas": int(area["population_2018"].notna().sum()), "units": float(area["units"].sum()),
                      "crash_total": float(area["crash_total"].sum()), "rho": rho}
    return report


def findings_text(report, measure_label, housing_label):
    """A few short sentences about the current report. They describe patterns and never claim a cause."""
    if report.get("empty"):
        return ["No ZIP areas match this selection."]
    out = []
    rho, n = report["rho"], report["n_corr"]
    if pd.isna(rho):
        out.append(f"Only {n} areas are selected, which is too few to describe an association reliably.")
    else:
        out.append(f"Across {n} ZIP areas, {housing_label.lower()} affordable units completed per resident and "
                   f"{measure_label.lower()} per 100,000 residents per year show a {describe_strength(rho)} (Spearman ρ = {rho:.2f}). "
                   "This describes areas, not individual residents, and does not show cause and effect.")
    q = report["area"]["quadrant"].value_counts()
    out.append(f"{int(q.get(QUADRANTS[0], 0))} areas combine upper-half affordable production with an at-or-above-median crash rate.")
    t = report["types"]["median_crash_rate"]
    if pd.notna(t.get("New-construction dominant")) and pd.notna(t.get("Preservation dominant")):
        out.append(f"Median crash rate: {t['New-construction dominant']:.1f} in new-construction-dominant areas vs "
                   f"{t['Preservation dominant']:.1f} in preservation-dominant areas (a descriptive difference).")
    top = report["priority"]
    if len(top):
        out.append("Highest-scoring candidate areas for further investigation: " + ", ".join(top["modzcta"].head(3)) + ".")
    return out


# Reading the files saved by the notebook (used by the website and by the check in notebook Section 13.3)

APP_FILES = {"panel": "panel_modzcta_year.csv", "crashes": "crashes_for_app.csv", "pipeline": "area_pipeline.csv",
             "coverage": "borough_year_summary.csv", "buildings": "buildings_for_app.csv",
             "geojson": "modzcta_simplified.geojson", "meta": "metadata.json"}


def missing_app_files(data_dir):
    """Names of the required data files that are missing from data_dir."""
    return [name for name in APP_FILES.values() if not (Path(data_dir) / name).exists()]


def load_app_data(data_dir):
    """Read the processed files once. ZIP-area codes are read as text, so "10001" stays "10001"."""
    d = Path(data_dir)
    as_text = {"modzcta": str}
    return {"panel": pd.read_csv(d / APP_FILES["panel"], dtype=as_text),
            "crashes": pd.read_csv(d / APP_FILES["crashes"], dtype=as_text),
            "pipeline": pd.read_csv(d / APP_FILES["pipeline"], dtype=as_text),
            "coverage": pd.read_csv(d / APP_FILES["coverage"]),
            "buildings": pd.read_csv(d / APP_FILES["buildings"], dtype=as_text),
            "geojson": json.loads((d / APP_FILES["geojson"]).read_text()),
            "meta": json.loads((d / APP_FILES["meta"]).read_text())}
