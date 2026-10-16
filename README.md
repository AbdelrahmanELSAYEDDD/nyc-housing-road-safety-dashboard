# Affordable Housing Development and Road Safety in New York City

Data Engineering and Visualization · German International University (GIU) · Winter Semester 2026 · Project Milestone 1
Repository: `nyc-housing-road-safety-dashboard`

**Main question.** Do New York City areas with more affordable housing production also have higher serious traffic-crash rates,
and how does this change across locations, years, construction types and income groups?

We clean and combine one housing dataset and one transportation dataset from NYC Open Data by **ZIP-code area and year
(2022–2025)**, answer eight research questions in a Google Colab notebook, and show the results on an interactive **Dash** website
with dropdown filters, a keyword search, a **Generate Report** button and a data story.

| | |
|---|---|
| Website | https://succeeds-salmon-pheasant-b62dfbf3.plotly.app/|
| Notebook | `notebooks/01_data_engineering_and_visualization_FINAL_SUBMISSION.ipynb` |
| Student | Abdelrahman El-sayed (13004550) — see [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |
| AI assistance | ChatGPT (OpenAI) for planning, explanations and reviews; Claude (Anthropic) for most of the code — see [CONTRIBUTIONS.md](CONTRIBUTIONS.md) and [docs/AI_PROMPT_LOG.md](docs/AI_PROMPT_LOG.md) |

## Datasets

| Role | Dataset | ID | Link |
|---|---|---|---|
| Housing & Development | Affordable Housing Production by Building (H2), HPD | `hg8x-zxpr` | https://data.cityofnewyork.us/d/hg8x-zxpr |
| Transportation | Serious Injury Response, Tracking & Analysis Program — SIRTA (T4), DOT | `xeqp-qz8h` | https://data.cityofnewyork.us/d/xeqp-qz8h |
| Geographic reference only | Modified ZIP Code Tabulation Areas — MODZCTA, DOHMH | `pri4-ifjk` | https://data.cityofnewyork.us/d/pri4-ifjk |

* **H2**: one row per building in an HPD-financed affordable housing project (new construction or preservation), with unit counts
  by income band, completion dates, ZIP code and coordinates (9,551 rows × 41 columns in October 2026).
* **SIRTA**: one row per serious crash (someone killed or seriously injured) reviewed by DOT, with date, time, injuries, ZIP code,
  coordinates and a 3-year look-back field (13,754 rows × 23 columns in October 2026).
* **MODZCTA** gives the ZIP-area boundaries (to place records by their coordinates) and 2018 population estimates (for rates per
  resident). It is used only for geographic matching, maps and population. **The TA has not yet confirmed whether this is allowed
  under the "exactly two datasets" rule.**

## The eight research questions

| Section | Question | Chart |
|---|---|---|
| A — Spatial relationship | **RQ1** Is affordable housing production associated with serious traffic-crash rates across NYC areas? | Scatter plot |
| | **RQ2** Which areas have both relatively high affordable housing production and relatively high serious-crash rates? | Map |
| B — Time patterns | **RQ3** How did serious crashes change between 2022 and 2025 across areas with different levels of affordable housing production? | Line chart |
| | **RQ4** How do crash times and weekdays differ between areas with different housing-production levels? | Heatmap |
| C — Housing characteristics | **RQ5** Do areas dominated by new construction and preservation show different serious-crash patterns? | Box plot |
| | **RQ6** Are affordable housing units in different income categories located in areas with different serious-crash rates? | Bar chart |
| D — Road-safety priorities | **RQ7** Do areas with greater affordable housing production also have higher shares of crashes with reported historical similar serious-injury or fatality events? | Stacked bar chart |
| | **RQ8** Which areas combine unfinished affordable housing projects with relatively high serious-crash rates? | Ranked bar chart |

The results describe areas, not individual people, and show associations, not causes.

## Folder structure

```
app.py                  the Dash website (one page)
src/analysis.py         calculations for the eight research questions (used by the notebook and the website)
src/figures.py          the eight charts (used by the notebook and the website)
assets/style.css        website layout
notebooks/              the final Google Colab notebook, with its outputs
data/processed/         cleaned and combined data saved by the notebook; the website reads these files
reports/                validation summary, cleaning log, data problems, record ledger, limitations and the data story
tests/                  automated checks (pytest)
docs/AI_PROMPT_LOG.md   the AI prompts used in the project
CONTRIBUTIONS.md        who did what
requirements.txt        website libraries (fixed versions)
render.yaml, .python-version   Render settings (Python 3.12)
```

## 1. Run the notebook (Google Colab)

1. Open https://colab.research.google.com → **File → Upload notebook** → choose the notebook in `notebooks/`.
2. **Runtime → Run all** (a normal CPU runtime is enough). The notebook downloads the three datasets from the NYC Open Data API and
   checks that every row was downloaded.
3. In **Section 13.1** there must be no `FAIL`.
4. In the last cell of Section 13, set `DOWNLOAD_BUNDLE = True` and run it. Unzip the downloaded `processed_outputs.zip` in the
   repository root: it updates `data/processed/` and `reports/`.

The notebook in this repository is saved with the outputs of the final run (16 October 2026). Its interactive charts show in
Colab or Jupyter; GitHub's notebook preview does not run JavaScript, so the charts appear blank there.

## 2. Run the website on your computer

Requires Python 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python app.py                   # then open http://127.0.0.1:8050
```

To run the automated checks: `pip install pytest`, then `python -m pytest -q`.

## 3. Using the website

* **Dropdowns:** Borough, Year, Construction type, Crash measure (serious crashes / severe injuries / fatalities) and Roads
  (local streets / all roads including highways).
* **Search:** type words such as `Brooklyn 2023 new construction` or `Bronx fatalities 2022-2024` and press Enter. The search fills
  in the dropdowns; words it does not recognise (for example `2026`) are listed back to you.
* **Generate Report** recalculates the summary figures, the findings and all eight charts with the same code as the notebook.
  Charts support hover, zoom and pan.
* **Data story** (bottom of the page): the question, the data, the main findings, what surprised us, the limitations and why it
  matters for New York City.

## 4. Files needed for deployment

The website only needs: `app.py`, `src/`, `assets/`, `requirements.txt`, `render.yaml`, `.python-version` and these seven files
in `data/processed/`: `panel_modzcta_year.csv`, `crashes_for_app.csv`, `buildings_for_app.csv`, `area_pipeline.csv`,
`borough_year_summary.csv`, `modzcta_simplified.geojson`, `metadata.json`. It reads them once at start-up and never downloads data,
so it does not need Google Colab, Google Drive or a database.

## 5. Deploy on Render (free)

1. Upload this repository to GitHub.
2. Sign in at https://dashboard.render.com with GitHub → **New → Blueprint** → choose the repository → **Apply**.
   Render reads `render.yaml`: build `pip install -r requirements.txt`, start `gunicorn app:server --workers 1 --timeout 120`,
   free plan, Python 3.12 from `.python-version`.
   (Without the Blueprint: **New → Web Service**, Language Python 3, the same build and start commands, instance type Free.)
3. When the log says the service is live, open the `https://….onrender.com` link and test it (section 3).
4. Put the link in the table at the top of this README.

Free services sleep after 15 minutes without visitors; the first visit after that can take about a minute.

## 6. Testing status

Checked on 16 October 2026, before uploading to GitHub. The local tests were run by Claude (AI) while packaging the repository.

| Check | Result |
|---|---|
| Final notebook in Google Colab (real NYC Open Data, fresh download) | 81 of 81 code cells ran without errors; validation **76 PASS, 0 WARN, 0 FAIL**; 708 area-year rows; all eight research charts |
| Processed data (`processed_outputs.zip` from the same run) | Totals reconcile: 11,958 serious crashes 2022–2025 (10,777 placed in a ZIP area; 28 with the borough taken from their ZIP area, all in Queens; 8 with an unknown borough) and 101,249 completed units (100,057 in ZIP areas + 1,192 in confidential buildings) |
| Automated tests (`python -m pytest -q`) | 17 passed. They use small hand-made test data, not the real data, and also check that the notebook's code cells are identical to `src/analysis.py` and `src/figures.py` |
| Website vs notebook | The website's default report, recalculated from `data/processed/`, matches the notebook's `reports/results_summary.json` on all 27 compared values (RQ1–RQ8) |
| Website in a browser (local, real data, started with gunicorn as on Render, headless Chromium) | Page loads; all 8 charts drawn after every action; search (button and Enter key), the five dropdowns and Generate Report work; empty selections and unknown words are explained; story shows the "What surprised us" paragraph; no browser errors; fits a 390-pixel phone screen |

**Not tested yet:** the GitHub upload, the Render build and the public website (including speed and memory on Render's free
plan), and other browsers such as Firefox, Safari and real phones. Do these checks after section 5 and record the result here.

## 7. Development history and AI documentation

* **Section 14 of the notebook** describes the 15 development stages, the roles of the student, ChatGPT and Claude, and the testing status.
* **[CONTRIBUTIONS.md](CONTRIBUTIONS.md)** describes the student's contributions and how ChatGPT and Claude were used. Only one
  contributor is documented; the Project Description expects four members who each propose two research questions, so this
  **needs clarification from the instructor/TA**.
* **[docs/AI_PROMPT_LOG.md](docs/AI_PROMPT_LOG.md)** starts with a short development record and prompt log, followed by the seven
  prompts sent to Claude, word for word. The exact ChatGPT prompts are not available; the log summarises them instead.

## 8. Submission (from the Project Description)

One email to ICS503Data@gmail.com with the member IDs, the GitHub repository link, the website link and the dataset links above,
before 9 November 2026.
