"""Dash website: Affordable Housing Development and Road Safety in New York City.

Single page with dropdown filters, a keyword search, a Generate Report button, eight research-question charts and a
data story. All numbers are computed by src/analysis.py from the files the notebook saves in data/processed/,
using exactly the same functions as the notebook. The website never downloads the original datasets.

Run locally:   python app.py            (http://127.0.0.1:8050)
Production:    gunicorn app:server
"""
import os
from pathlib import Path

from dash import Dash, Input, Output, State, dcc, html

from src.analysis import (BOROUGHS, CRASH_MEASURES, CRASH_SCOPES, DEFAULT_FILTERS, HOUSING_TYPES, YEARS, build_report,
                          compute_area_metrics, describe_strength, findings_text, load_app_data, merge_filters, missing_app_files,
                          parse_search, spearman)
from src.figures import report_figures

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent / "data" / "processed"))
MISSING_FILES = missing_app_files(DATA_DIR)
DATA = None if MISSING_FILES else load_app_data(DATA_DIR)          # read once at start-up, never per request

HOUSING_LABELS = {"All": "All construction types", "New Construction": "New construction", "Preservation": "Preservation"}
SOURCES = [("Affordable Housing Production by Building (H2) — HPD", "https://data.cityofnewyork.us/d/hg8x-zxpr"),
           ("Serious Injury Response, Tracking & Analysis Program — SIRTA (T4) — DOT", "https://data.cityofnewyork.us/d/xeqp-qz8h"),
           ("MODZCTA ZIP-code areas (geographic reference only) — DOHMH", "https://data.cityofnewyork.us/d/pri4-ifjk")]
RQ_TEXT = {
    1: ("Is affordable housing production associated with serious traffic-crash rates across NYC areas?",
        "Each bubble is a ZIP area. Spearman ρ summarises whether areas ranked higher on one measure also rank higher on the other. "
        "It describes areas, not residents, and does not show cause and effect."),
    2: ("Which areas have both relatively high affordable housing production and relatively high serious-crash rates?",
        "Areas are coloured by combining their production tier with their crash rate; dots are completed buildings. Zoom and hover for values."),
    3: ("How did serious crashes change between 2022 and 2025 across areas with different levels of affordable housing production?",
        "Indexed to the first selected year = 100. Tiers use units completed in the same years, so this is a description, not an effect. "
        "The lower panel shows how many crashes could be placed in an area each year."),
    4: ("How do crash times and weekdays differ between areas with different housing-production levels?",
        "Difference in the share of crashes per weekday × time cell (upper-half production areas minus all other areas). "
        "Counts crashes; crashes logged at exactly 00:00 are excluded. Exploratory."),
    5: ("Do areas dominated by new construction and preservation show different serious-crash patterns?",
        "New-construction dominant: more than 60% of completed units are new construction; preservation dominant: less than 40%."),
    6: ("Are affordable housing units in different income categories located in areas with different serious-crash rates?",
        "Rate of the area where the average unit of each income band was completed, compared with the average resident. "
        "This describes locations, not personal risk."),
    7: ("Do areas with greater affordable housing production also have higher shares of crashes with reported historical similar "
        "serious-injury or fatality events?",
        "DOT's look-back field counts fatalities and severe injuries in same-type crashes at the same location in the previous three years. "
        "Blank values are shown as unknown, never as zero. Local-street crashes only."),
    8: ("Which areas combine unfinished affordable housing projects with relatively high serious-crash rates?",
        "Score = average of two percentiles (unfinished units per resident, crash rate). A screening list for further investigation, "
        "not a prediction. Unfinished projects are counted at the data snapshot, so the year filter changes only the crash rate."),
}
SECTIONS = [("A — Spatial relationship", [1, 2]), ("B — Time patterns", [3, 4]),
            ("C — Housing characteristics", [5, 6]), ("D — Road-safety priorities", [7, 8])]

app = Dash(__name__, title="NYC Affordable Housing & Road Safety")
server = app.server          # used by gunicorn on Render


def describe_filters(f):
    boroughs = "All boroughs" if len(f["boroughs"]) == len(BOROUGHS) else ", ".join(f["boroughs"])
    years = f"{f['years'][0]}–{f['years'][-1]}" if f["years"] == list(range(f["years"][0], f["years"][-1] + 1)) and len(f["years"]) > 1 \
        else ", ".join(map(str, f["years"]))
    return " · ".join([boroughs, years, HOUSING_LABELS[f["housing_type"]], CRASH_MEASURES[f["crash_measure"]], CRASH_SCOPES[f["crash_scope"]]])


def kpi_cards(report):
    f = report["filters"]
    k = report.get("kpis", {"areas": 0, "units": 0, "crash_total": 0, "rho": float("nan")})
    rho = k["rho"]
    cards = [("ZIP areas", f"{k['areas']:,}", "with a population estimate"),
             ("Affordable units completed", f"{k['units']:,.0f}", HOUSING_LABELS[f["housing_type"]].lower()),
             (f"{CRASH_MEASURES[f['crash_measure']]}", f"{k['crash_total']:,.0f}", f"{CRASH_SCOPES[f['crash_scope']].lower()}, placed in a ZIP area"),
             ("RQ1 rank correlation", "n/a" if rho != rho else f"{rho:.2f}", describe_strength(rho))]
    return [html.Div([html.Div(label, className="kpi-label"), html.Div(value, className="kpi-value"),
                      html.Div(note, className="kpi-note")], className="kpi") for label, value, note in cards]


def surprise_text(default):
    """'What surprised us': the same approved wording as the notebook's data story, filled in with the same calculations
    (RQ1 for new construction and preservation separately, and the RQ5 medians). If newer data no longer show this
    pattern, the numbers are shown without the interpretation."""
    def num(value, spec=".1f"):
        return "n/a" if value is None or value != value else format(value, spec)
    rho = {}
    for housing_type in ("New Construction", "Preservation"):
        area = compute_area_metrics(DATA["panel"], housing_type=housing_type)
        rho[housing_type] = round(spearman(area["units_per_1k"], area["crash_rate"])[0], 3)
    rho_nc, rho_pres = rho["New Construction"], rho["Preservation"]
    medians = default["types"]["median_crash_rate"]
    med_nc, med_pres = medians.get("New-construction dominant", float("nan")), medians.get("Preservation dominant", float("nan"))
    if rho_nc > rho_pres and med_nc > med_pres:
        return ("One finding that stood out was the difference between new construction and preservation. Areas with more "
                f"new-construction units per resident tended to have higher serious-crash rates (ρ = {num(rho_nc, '.2f')}), while "
                f"preservation showed a much weaker relationship (ρ = {num(rho_pres, '.2f')}). We also found that new-construction-dominant "
                f"areas had a higher median crash rate ({num(med_nc)}) than preservation-dominant areas ({num(med_pres)}). This is an "
                "interesting difference, but it does not mean that new construction causes more crashes.")
    return (f"New construction and preservation compared: ρ = {num(rho_nc, '.2f')} for new-construction units per resident and "
            f"ρ = {num(rho_pres, '.2f')} for preservation; median crash rate {num(med_nc)} in new-construction-dominant areas and "
            f"{num(med_pres)} in preservation-dominant areas. These are descriptive differences, not causes.")


def static_story():
    """Story text. The findings are computed from the data at start-up (default selection), never typed in by hand."""
    if DATA is None:
        return []
    default = build_report(DATA, DEFAULT_FILTERS)
    found = findings_text(default, CRASH_MEASURES["crashes"], "All")
    return [
        html.H2("Data story"),
        html.Div([
            html.Div([html.H3("The question"), html.P(
                "Do New York City areas that produce more affordable housing also have more serious traffic crashes per resident — and how "
                "does this differ by place, year, construction type and income group? Affordable homes are built or preserved to house people "
                "for decades; if they are concentrated where streets are most dangerous, housing and road-safety planning could be coordinated.")]),
            html.Div([html.H3("The data and how it was connected"), html.P(
                "HPD's Affordable Housing Production by Building (completed and unfinished affordable units, new construction and preservation) "
                "and DOT's SIRTA serious-crash records. Both were cleaned, placed in ZIP-code areas (by coordinates first, ZIP code otherwise) "
                "and added up per ZIP area and year for 2022–2025, then joined one-to-one. Per-resident rates use the 2018 population of each area.")]),
        ], className="story-grid"),
        html.H3("Main findings (all boroughs, 2022–2025, serious crashes on local streets)"),
        html.Ul([html.Li(s) for s in found]),
        html.H3("What surprised us"),
        html.P(surprise_text(default)),
        html.Div([
            html.Div([html.H3("Limitations"), html.Ul([
                html.Li("Correlation is not causation: these are area-level associations, not effects of housing and not individual risk."),
                html.Li("Preservation rehabilitates existing homes and does not necessarily add residents."),
                html.Li("Rates use 2018 population estimates; areas with few residents but heavy traffic have very high per-resident rates."),
                html.Li("Some crashes and all confidential buildings could not be placed in a ZIP area; SIRTA covers serious crashes only."),
                html.Li("Four years (2022–2025) describe change but cannot establish trends; 2026 is incomplete and excluded."),
                html.Li("MODZCTA is used only as a geographic reference; its acceptability is pending TA confirmation."),
            ])]),
            html.Div([html.H3("Why it matters for New York City"), html.P(
                "The overlap areas (RQ2) and the screening list (RQ8) show where DOT and HPD could look first when reviewing street safety "
                "around new and renovated affordable homes, and community boards can explore their own borough and years. Any action should "
                "start with a closer local look, because these figures identify places to investigate, not causes.")]),
        ], className="story-grid"),
    ]


def control_panel():
    return html.Div([
        html.Label("Search", htmlFor="search", className="control-label"),
        html.Div([
            dcc.Input(id="search", type="text", debounce=True, placeholder='e.g. "Brooklyn 2023 new construction" or "Bronx fatalities 2022-2024"',
                      className="search-input"),
            html.Button("Generate Report", id="generate", n_clicks=0, className="generate-button"),
        ], className="search-row"),
        html.Div("Recognised words: borough names, years 2022–2025 (or a range such as 2022-2024), new construction / preservation, "
                 "crashes / severe injuries / fatalities, local streets / highways. Press Enter or click Generate Report.", className="hint"),
        html.Div([
            html.Div([html.Label("Borough", className="control-label"),
                      dcc.Dropdown(id="f-borough", options=BOROUGHS, value=list(BOROUGHS), multi=True, placeholder="All boroughs")]),
            html.Div([html.Label("Year", className="control-label"),
                      dcc.Dropdown(id="f-year", options=YEARS, value=list(YEARS), multi=True, placeholder="All years")]),
            html.Div([html.Label("Construction type (housing)", className="control-label"),
                      dcc.Dropdown(id="f-housing", options=[{"label": v, "value": k} for k, v in HOUSING_LABELS.items()],
                                   value="All", clearable=False)]),
            html.Div([html.Label("Crash measure (transportation)", className="control-label"),
                      dcc.Dropdown(id="f-measure", options=[{"label": v, "value": k} for k, v in CRASH_MEASURES.items()],
                                   value="crashes", clearable=False)]),
            html.Div([html.Label("Roads", className="control-label"),
                      dcc.Dropdown(id="f-scope", options=[{"label": v, "value": k} for k, v in CRASH_SCOPES.items()],
                                   value="local", clearable=False)]),
        ], className="filter-grid"),
        html.Div(id="feedback", className="feedback", role="status"),
    ], className="card controls")


def chart_sections():
    blocks = []
    for name, rqs in SECTIONS:
        cards = []
        for i in rqs:
            question, note = RQ_TEXT[i]
            cards.append(html.Div([html.H3(f"RQ{i}. {question}"), html.P(note, className="note"),
                                   dcc.Loading(dcc.Graph(id=f"rq{i}", config={"displaylogo": False, "responsive": True}))],
                                  className="card chart-card"))
        blocks.append(html.Section([html.H2(f"Section {name}"), html.Div(cards, className="chart-grid")]))
    return blocks


def layout():
    meta = DATA["meta"] if DATA else {}
    header = html.Header([
        html.H1("Affordable Housing Development and Road Safety in New York City"),
        html.P("Data Engineering and Visualization · German International University · Winter Semester 2026 · Project Milestone 1",
               className="subtitle"),
        html.P(f"Data snapshot: {meta.get('snapshot_date', 'not available')} · ZIP-code areas × years 2022–2025", className="meta")
        if DATA else None,
    ])
    if DATA is None:
        return html.Main([header, html.Div([
            html.H2("Processed data files are missing"),
            html.P("Run the notebook in Google Colab, download processed_outputs.zip and unzip it in the repository root so that "
                   "these files exist in data/processed/:"),
            html.Ul([html.Li(name) for name in MISSING_FILES]),
        ], className="card warning")], className="page")
    test_banner = (html.Div("Test data: these files were produced from local test files, not from NYC Open Data. "
                            "Do not use these numbers.", className="card warning")
                   if meta.get("source_mode") == "offline-test" else None)
    return html.Main([
        header, test_banner,
        control_panel(),
        html.Div(id="report-title", className="report-title"),
        html.Div(id="kpis", className="kpi-row"),
        html.Div([html.H3("Findings for this selection"), html.Ul(id="selection-findings")], className="card findings"),
        *chart_sections(),
        html.Section(static_story(), className="card story"),
        html.Footer([
            html.H3("Data sources"),
            html.Ul([html.Li(html.A(label, href=url, target="_blank", rel="noopener")) for label, url in SOURCES]),
            html.P("Responsible contributor: Abdelrahman El-sayed (13004550). Other team members: not yet assigned. "
                   "Code and analysis were developed with AI assistance (Claude, Anthropic); see docs/AI_PROMPT_LOG.md in the repository."),
        ], className="footer"),
    ], className="page")


app.layout = layout()          # built once at start-up (the story's findings are computed from the data here)

DROPDOWNS = ["f-borough", "f-year", "f-housing", "f-measure", "f-scope"]


@app.callback(
    [Output(d, "value") for d in DROPDOWNS] + [Output("search", "value"), Output("feedback", "children"), Output("report-title", "children"),
                                               Output("kpis", "children"), Output("selection-findings", "children")]
    + [Output(f"rq{i}", "figure") for i in range(1, 9)],
    Input("generate", "n_clicks"), Input("search", "n_submit"),
    [State(d, "value") for d in DROPDOWNS] + [State("search", "value")],
)
def generate_report(n_clicks, n_submit, boroughs, years, housing_type, crash_measure, crash_scope, query):
    """Generate Report: read the dropdowns, apply any search words on top of them, recompute every chart."""
    messages = []
    if not boroughs:
        messages.append("No borough was selected, so all boroughs are shown.")
    if not years:
        messages.append("No year was selected, so all years 2022–2025 are shown.")
    parsed = parse_search(query)
    if query and query.strip():
        if parsed["recognized"]:
            messages.append("Search applied: " + ", ".join(f"“{w}”" for w in parsed["recognized"]) + ".")
        if parsed["ignored"]:
            messages.append("Not used: " + ", ".join(f"“{w}”" for w in parsed["ignored"])
                            + " (only borough names, years 2022–2025, construction types, crash measures and road types are recognised).")
        if not parsed["recognized"]:
            messages.append("No filter words were recognised, so the dropdown selections were used.")
    filters = merge_filters({"boroughs": boroughs, "years": years, "housing_type": housing_type,
                             "crash_measure": crash_measure, "crash_scope": crash_scope}, parsed)
    report = build_report(DATA, filters)
    findings = findings_text(report, CRASH_MEASURES[filters["crash_measure"]], filters["housing_type"])
    figures = report_figures(report, DATA["geojson"])
    title = [html.Span("Report: ", className="report-label"), describe_filters(filters)]
    return ([filters["boroughs"], filters["years"], filters["housing_type"], filters["crash_measure"], filters["crash_scope"], "",
             " ".join(messages), title, kpi_cards(report), [html.Li(s) for s in findings]] + figures)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=int(os.environ.get("PORT", 8050)))
