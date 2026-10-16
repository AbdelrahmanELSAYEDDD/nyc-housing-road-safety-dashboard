"""The eight research-question charts, used by both the notebook and the Dash website.

Each function takes tables from src/analysis.py and returns a Plotly figure.
If a selection leaves nothing to show, the function returns an empty chart with a short message.
"""
import textwrap

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis import BAND_LABELS, BLOCKS, CRASH_MEASURES, DAYS, QUADRANTS, TIER_ORDER, TYPE_ORDER, describe_strength

# Chart colours. They are easy to tell apart, also for colour-blind readers.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
NEUTRAL, INK, INK_SOFT, SURFACE, GRID = "#b8b6ae", "#0b0b0b", "#52514e", "#fcfcfb", "#e7e6e2"
TIER_COLORS = {"No completions": NEUTRAL, "Lower half": SERIES[0], "Upper half": SERIES[1]}
QUADRANT_COLORS = dict(zip(QUADRANTS, [SERIES[7], SERIES[0], SERIES[1], "#e7e6e2"]))
DIVERGING = [[0.0, "#2a78d6"], [0.5, "#f0efec"], [1.0, "#e34948"]]
RATE_WORDING = {"Serious crashes": "serious-crash rate", "Severe injuries": "severe-injury rate", "Fatalities": "fatality rate"}
HOUSING_WORDING = {"All": "new construction + preservation", "New Construction": "new construction only", "Preservation": "preservation only"}


def style(fig, title, subtitle=None, height=440):
    """Common look for all charts: a bold title, a grey subtitle (split into lines so it fits), light background."""
    title_lines = textwrap.wrap(title, 72, break_on_hyphens=False)
    sub_lines = textwrap.wrap(subtitle, 100, break_on_hyphens=False) if subtitle else []
    text = "<br>".join(f"<b>{line}</b>" for line in title_lines)
    if sub_lines:
        text += "<br>" + "<br>".join(f"<span style='font-size:12px;color:{INK_SOFT}'>{line}</span>" for line in sub_lines)
    top = 36 + 19 * len(title_lines) + 16 * len(sub_lines)
    fig.update_layout(title=dict(text=text, x=0, xanchor="left", xref="container", y=1, yanchor="top", yref="container",
                                 pad=dict(t=14, l=12), font=dict(size=15, color=INK)),
                      height=height + top - 78, template="plotly_white",
                      font=dict(family="Arial, Helvetica, sans-serif", size=12, color=INK),
                      paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, margin=dict(l=60, r=24, t=top + 8, b=56),
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def empty_figure(title, message="No data for this selection"):
    """A blank chart with a message, used when the selection has nothing to show."""
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color=INK_SOFT))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style(fig, title, height=320)


def rate_words(measure_label):
    """Words for the selected measure, e.g. "serious-crash rate" or "fatality rate"."""
    return RATE_WORDING.get(measure_label, f"{measure_label.lower()} rate")


def fig_rq1(area, rho, n, measure_label="Serious crashes", housing_label="All"):
    """RQ1 scatter plot: units completed per 1,000 residents (x, log scale) against the crash rate (y), one bubble per area."""
    title = f"RQ1 · Affordable units completed per resident vs {rate_words(measure_label)}"
    d = area.dropna(subset=["crash_rate", "production_tier"])
    if d.empty:
        return empty_figure(title)
    pos = d.loc[d["units_per_1k"] > 0, "units_per_1k"]
    lo = int(np.floor(np.log10(pos.min()))) if len(pos) else -1
    hi = int(np.ceil(np.log10(pos.max()))) if len(pos) else 1
    # A log axis cannot show 0, so areas with no completed units are drawn just left of the
    # smallest value, and that position is labelled "0" on the axis.
    zero_x = 10 ** (lo - 0.5)
    d = d.assign(x_plot=d["units_per_1k"].where(d["units_per_1k"] > 0, zero_x), population_2018=d["population_2018"].astype(float))
    fig = px.scatter(d, x="x_plot", y="crash_rate", color="production_tier", size="population_2018", size_max=20, log_x=True,
                     category_orders={"production_tier": TIER_ORDER}, color_discrete_map=TIER_COLORS,
                     custom_data=["modzcta", "area_borough", "units", "crash_total", "population_2018", "units_per_1k"],
                     labels={"x_plot": f"Units completed per 1,000 residents ({HOUSING_WORDING.get(housing_label, housing_label)}, log)",
                             "crash_rate": f"{measure_label} per 100,000 residents per year", "production_tier": "Production tier"})
    fig.update_traces(marker=dict(line=dict(width=1, color=SURFACE), opacity=0.85),
                      hovertemplate="<b>ZIP area %{customdata[0]}</b> (%{customdata[1]})<br>Units completed: %{customdata[2]:,.0f}"
                                    "<br>Units per 1,000 residents: %{customdata[5]:.2f}<br>" + measure_label +
                                    ": %{customdata[3]:,.0f}<br>Rate: %{y:.1f} per 100k per year<br>Population (2018): %{customdata[4]:,.0f}<extra></extra>")
    ticks = [zero_x] + [10 ** k for k in range(lo, hi + 1)]
    fig.update_xaxes(tickvals=ticks, ticktext=["0"] + [f"{v:g}" for v in ticks[1:]])
    sub = (f"Spearman ρ = {rho:.2f} across {n} areas ({describe_strength(rho)}). Bubble size = 2018 population; "
           "areas with no completed units are shown at '0'." if pd.notna(rho) else f"Too few areas ({n}) to measure an association.")
    return style(fig, title, sub, height=480)


def map_view(geojson, codes, width_px=600, height_px=470):
    """Centre and zoom of the map, so the selected areas fill it (one borough is shown close up)."""
    lons, lats = [], []
    for feature in geojson["features"]:
        if feature["properties"].get("modzcta") in codes:
            geom = feature["geometry"]
            polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            points = np.array([pt for polygon in polygons for ring in polygon for pt in ring], dtype=float)
            lons += [points[:, 0].min(), points[:, 0].max()]
            lats += [points[:, 1].min(), points[:, 1].max()]
    if not lons:
        return {"lat": 40.705, "lon": -73.94}, 9.0
    lon_span, lat_span = max(lons) - min(lons), max(lats) - min(lats)
    mid_lat = (max(lats) + min(lats)) / 2
    zoom_lon = np.log2(width_px * 360 / (512 * max(lon_span, 0.01)))
    zoom_lat = np.log2(height_px * 360 * np.cos(np.radians(mid_lat)) / (512 * max(lat_span, 0.01)))
    return {"lat": mid_lat, "lon": (max(lons) + min(lons)) / 2}, float(min(zoom_lon, zoom_lat) - 0.2)


def fig_rq2(area, crash_median, geojson, buildings=None, measure_label="Serious crashes"):
    """RQ2 map: areas coloured by production tier and crash rate, with completed buildings drawn on top."""
    title = f"RQ2 · Where high affordable production meets a high {rate_words(measure_label)}"
    d = area.dropna(subset=["quadrant"])
    if d.empty:
        return empty_figure(title)
    d = d.assign(units_per_1k_r=d["units_per_1k"].round(2), crash_rate_r=d["crash_rate"].round(1))
    center, zoom = map_view(geojson, set(d["modzcta"]))
    # The map has a plain background instead of map tiles, so it works without an outside map service.
    common = dict(geojson=geojson, locations="modzcta", featureidkey="properties.modzcta", color="quadrant",
                  category_orders={"quadrant": QUADRANTS}, color_discrete_map=QUADRANT_COLORS, hover_name="modzcta",
                  hover_data={"area_borough": True, "units": ":,.0f", "units_per_1k_r": True, "crash_rate_r": True,
                              "quadrant": False, "modzcta": False},
                  labels={"quadrant": "Area type", "area_borough": "Borough", "units": "Units completed",
                          "units_per_1k_r": "Units per 1,000 residents", "crash_rate_r": f"{measure_label} per 100k per year"},
                  center=center, zoom=zoom, opacity=0.8)
    use_maplibre = hasattr(px, "choropleth_map")          # newer Plotly (5.24+); older versions use the Mapbox version
    fig = (px.choropleth_map(d, map_style="white-bg", **common) if use_maplibre
           else px.choropleth_mapbox(d, mapbox_style="white-bg", **common))
    if buildings is not None and len(buildings):
        trace = go.Scattermap if use_maplibre else go.Scattermapbox
        max_units = float(buildings["units_counted"].max())
        for ctype, colour in [("New Construction", INK), ("Preservation", SERIES[6])]:
            b = buildings[buildings["construction_type"].eq(ctype)]
            if b.empty:
                continue
            size = 3 + 9 * np.sqrt(b["units_counted"].fillna(1).astype(float) / max_units)
            fig.add_trace(trace(lat=b["latitude"].astype(float), lon=b["longitude"].astype(float), mode="markers",
                                name=f"{ctype} buildings", marker=dict(size=size, color=colour, opacity=0.6), hoverinfo="text",
                                text=[f"{ctype}: {int(u):,} units · completed {int(y)}" for u, y in
                                      zip(b["units_counted"].fillna(0), b["completion_year"])]))
    fig.update_traces(marker_line_color="#ffffff", marker_line_width=0.6, selector=dict(type="choroplethmap"))
    fig = style(fig, title, f"High production = upper half of areas with completions; high rate = at or above the median "
                            f"area ({crash_median:.1f} per 100k per year). Scroll to zoom, drag to pan.", height=600)
    fig.update_layout(margin=dict(l=8, r=8, t=fig.layout.margin.t, b=8),
                      legend=dict(orientation="h", yanchor="top", y=-0.01, xanchor="left", x=0, title_text=""))
    return fig


def fig_rq3(trend, coverage, measure_label="Serious crashes"):
    """RQ3 line chart: crashes per production tier, indexed to the first year = 100, with the yearly placement rate below."""
    title = f"RQ3 · Change in {measure_label.lower()} by affordable production tier"
    if trend is None or trend.empty or trend["year"].nunique() < 2:
        return empty_figure(title, "Select at least two years to show change over time")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.1,
                        subplot_titles=(f"{measure_label}, indexed to {int(trend['year'].min())} = 100",
                                        "Share of crashes placed in a ZIP area (%)"))
    for tier in TIER_ORDER:
        d = trend[trend["tier"] == tier]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(x=d["year"], y=d["index"], mode="lines+markers", name=tier, line=dict(width=2, color=TIER_COLORS[tier]),
                                 marker=dict(size=8), customdata=d[["value", "areas"]],
                                 hovertemplate=f"<b>{tier}</b><br>%{{x}}: index %{{y:.1f}}<br>%{{customdata[0]:,.0f}} in %{{customdata[1]}} areas<extra></extra>"),
                      row=1, col=1)
    if coverage is not None and len(coverage):
        fig.add_trace(go.Bar(x=coverage["year"], y=coverage["assignment_rate_pct"], marker_color=NEUTRAL, showlegend=False,
                             hovertemplate="%{x}: %{y:.1f}% of crashes placed in an area<extra></extra>"), row=2, col=1)
    fig.add_hline(y=100, line_dash="dot", line_color=INK_SOFT, row=1, col=1)
    fig.update_xaxes(dtick=1, row=2, col=1, title_text="Year")
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    fig.update_layout(legend_title_text="Production tier")
    return style(fig, title, "Tiers are based on units completed in the same years, so this shows change, not cause", height=500)


def fig_rq4(cells):
    """RQ4 heatmap: difference in crash shares per weekday and time of day (upper-half areas minus other areas)."""
    title = "RQ4 · When serious crashes happen: upper-half production areas minus other areas"
    if cells is None or cells.attrs.get("n_upper", 0) == 0 or cells.attrs.get("n_other", 0) == 0:
        return empty_figure(title, "Not enough crashes with a known time in both groups")
    diff = cells.pivot(index="time_block", columns="weekday", values="diff_pp").loc[BLOCKS, DAYS]
    # Use the same colour range above and below zero, so white always means "no difference".
    zmax = float(np.nanmax(np.abs(diff.to_numpy()))) or 1.0
    fig = px.imshow(diff, color_continuous_scale=DIVERGING, zmin=-zmax, zmax=zmax, aspect="auto", text_auto=".1f",
                    labels=dict(x="Day of week", y="Time of day", color="Difference (pp)"))
    fig.update_traces(hovertemplate="%{x}, %{y}<br>Difference in share: %{z:.2f} percentage points<extra></extra>")
    return style(fig, title, f"Share of each group's crashes in each cell (each group adds up to 100%); {cells.attrs['n_upper']:,} vs "
                             f"{cells.attrs['n_other']:,} crashes. Small differences can be due to chance.", height=470)


def fig_rq5(area, types, measure_label="Serious crashes"):
    """RQ5 box plot: crash rates of the areas in each construction-type group."""
    title = f"RQ5 · {rate_words(measure_label).capitalize()} by the dominant type of affordable production"
    d = area.dropna(subset=["crash_rate"])
    if d.empty:
        return empty_figure(title)
    labels = {k: f"{k}<br>(n = {int(v)})" for k, v in types["areas"].fillna(0).items()}
    d = d.assign(group=d["dominant_type"].map(labels))
    fig = px.box(d, x="group", y="crash_rate", points="all", category_orders={"group": [labels[k] for k in TYPE_ORDER]},
                 color_discrete_sequence=[SERIES[0]], hover_data={"modzcta": True, "area_borough": True, "units": ":,.0f",
                                                                  "nc_share": ":.0%", "group": False},
                 labels={"group": "", "crash_rate": f"{measure_label} per 100,000 residents per year", "nc_share": "New-construction share"})
    fig.update_traces(marker=dict(size=6, opacity=0.6), line=dict(width=2))
    return style(fig, title, "New-construction dominant: > 60% of completed units are new construction; preservation dominant: < 40%")


def fig_rq6(bands, resident_avg, measure_label="Serious crashes", housing_type="All"):
    """RQ6 bar chart: crash rate where each income band's units were completed, with the average resident as a line."""
    title = f"RQ6 · {rate_words(measure_label).capitalize()} in the areas where units of each income band were completed"
    d = bands.dropna(subset=["weighted_crash_rate"])
    if d.empty:
        return empty_figure(title)
    fig = px.bar(d, x="weighted_crash_rate", y="band", orientation="h", color_discrete_sequence=[SERIES[0]], custom_data=["units"],
                 category_orders={"band": list(BAND_LABELS.values())}, text=d["weighted_crash_rate"].round(1),
                 labels={"weighted_crash_rate": f"{measure_label} per 100k residents per year (unit-weighted area average)", "band": ""})
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{y}</b><br>%{x:.1f} per 100k per year<br>Units: %{customdata[0]:,}<extra></extra>")
    if pd.notna(resident_avg):
        fig.add_vline(x=resident_avg, line_dash="dash", line_color=INK_SOFT, annotation_text=f"average resident: {resident_avg:.1f}",
                      annotation_position="top")
    note = "" if housing_type == "All" else " Income bands include both construction types."
    return style(fig, title, "Describes where units were completed, not the risk faced by residents." + note)


def fig_rq7(lookback):
    """RQ7 stacked bar chart: share of crashes with / without an earlier similar serious injury, per production tier."""
    title = "RQ7 · Crashes where DOT recorded earlier same-type serious injuries at the location (3-year look-back)"
    d = lookback.dropna(how="all", subset=["earlier_recorded", "none_recorded", "unknown"])
    if d.empty or d[["earlier_recorded", "none_recorded", "unknown"]].sum().sum() == 0:
        return empty_figure(title)
    plot = d[["earlier_recorded", "none_recorded", "unknown"]].rename(
        columns={"earlier_recorded": "Earlier similar serious injury recorded", "none_recorded": "None recorded", "unknown": "Unknown (blank)"})
    share = plot.div(plot.sum(axis=1), axis=0).mul(100)          # each tier adds up to 100%
    long = (share.reset_index(names="tier").melt(id_vars="tier", var_name="status", value_name="share")
            .merge(plot.reset_index(names="tier").melt(id_vars="tier", var_name="status", value_name="crashes"), on=["tier", "status"]))
    fig = px.bar(long, x="share", y="tier", color="status", orientation="h", barmode="stack", custom_data=["crashes"],
                 category_orders={"tier": TIER_ORDER[::-1], "status": list(plot.columns)},
                 color_discrete_map={"Earlier similar serious injury recorded": SERIES[1], "None recorded": SERIES[0], "Unknown (blank)": NEUTRAL},
                 text=[f"{v:.0f}%" if v >= 8 else "" for v in long["share"].fillna(0)],          # no labels in very thin segments
                 labels={"share": "Share of local-street serious crashes (%)", "tier": "Production tier", "status": ""})
    fig.update_traces(hovertemplate="%{y} · %{fullData.name}: %{x:.1f}% (%{customdata[0]:,} crashes)<extra></extra>",
                      marker_line_color=SURFACE, marker_line_width=2, textposition="inside", insidetextanchor="middle", textangle=0)
    return style(fig, title, "DOT's field counts deaths and severe injuries in same-type crashes at the same location in the previous 3 years",
                 height=380)


def fig_rq8(top, measure_label="Serious crashes"):
    """RQ8 ranked bar chart: the top areas with their two percentiles (unfinished units per resident and crash rate)."""
    title = "RQ8 · Candidate areas for further investigation: unfinished affordable projects and crash rates"
    if top is None or top.empty:
        return empty_figure(title, "No areas with unfinished affordable projects in this selection")
    t = top.assign(label=top["priority_rank"].astype(str) + ". " + top["modzcta"] + " · " + top["area_borough"])
    # One row per area and percentile, so the two bars of each area can be drawn side by side.
    long = t.melt(id_vars=["label", "priority_score", "pipeline_selected", "nc_pipeline_share", "crash_rate"],
                  value_vars=["pipeline_pct", "crash_pct"], var_name="component", value_name="percentile")
    long["component"] = long["component"].map({"pipeline_pct": "Unfinished units per resident", "crash_pct": rate_words(measure_label).capitalize()})
    fig = px.bar(long, x="percentile", y="label", color="component", orientation="h", barmode="group",
                 category_orders={"label": t["label"].tolist()}, color_discrete_sequence=SERIES[:2],
                 custom_data=["priority_score", "pipeline_selected", "nc_pipeline_share", "crash_rate"],
                 labels={"percentile": "Percentile among selected ZIP areas", "label": "", "component": ""})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:.0f}th percentile<br>Priority score %{customdata[0]:.1f}"
                                    "<br>Unfinished units: %{customdata[1]:,.0f} (%{customdata[2]:.0%} new construction overall)"
                                    "<br>Crash rate: %{customdata[3]:.1f} per 100k per year<extra></extra>",
                      marker_line_color=SURFACE, marker_line_width=2)
    fig.update_xaxes(range=[0, 100])
    return style(fig, title, "Score = average of the two percentiles. A list of places to look at more closely, not a prediction", height=560)


def report_figures(report, geojson):
    """The eight charts for one report from build_report (used by the website)."""
    f = report["filters"]
    measure = CRASH_MEASURES[f["crash_measure"]]
    if report.get("empty"):
        return [empty_figure(f"RQ{i}", "No ZIP areas match this selection") for i in range(1, 9)]
    return [fig_rq1(report["area"], report["rho"], report["n_corr"], measure, f["housing_type"]),
            fig_rq2(report["area"], report["crash_median"], geojson, report.get("buildings"), measure),
            fig_rq3(report["trend"], report["coverage"], measure),
            fig_rq4(report["time_cells"]),
            fig_rq5(report["area"], report["types"], measure),
            fig_rq6(report["bands"], report["resident_avg"], measure, f["housing_type"]),
            fig_rq7(report["lookback"]),
            fig_rq8(report["priority"], measure)]
