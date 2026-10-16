# Processed data (produced by the notebook)

These files are created by `notebooks/01_data_engineering_and_visualization_FINAL_SUBMISSION.ipynb` (Section 13) when it is run
in Google Colab on real NYC Open Data. Unzip `processed_outputs.zip` from the notebook in the repository root and they appear here.
The website needs the first seven files and reads them once at start-up.

| File | One row is | Used by |
|---|---|---|
| `panel_modzcta_year.csv` | one ZIP-code area (MODZCTA) in one year, 2022–2025: completed affordable units (new construction, preservation, income bands), serious crashes (local / all roads, severe injuries, fatalities, look-back status), 2018 population | all eight charts |
| `crashes_for_app.csv` | one serious crash placed in a ZIP area (hour, weekday, highway flag) | RQ4 |
| `area_pipeline.csv` | one ZIP area with unfinished affordable buildings (units by construction type) | RQ8 |
| `borough_year_summary.csv` | one borough-year: all crashes vs crashes placed in an area; units incl. confidential buildings. Crashes with no reported borough use the borough of their ZIP area (counted in `crashes_borough_derived`) or appear in an `Unknown` row, so the rows add up to all 2022–2025 crashes | RQ3 coverage panel |
| `buildings_for_app.csv` | one completed building (2022–2025) with coordinates | RQ2 map points |
| `modzcta_simplified.geojson` | one ZIP-area boundary | RQ2 map |
| `metadata.json` | snapshot date, source mode, row counts | website header |
| `housing_clean.csv`, `sirta_clean.csv` | cleaned record-level datasets with quality flags | reference (not loaded by the website) |

If `metadata.json` says `"source_mode": "offline-test"`, the files were made from local test files and the website shows a warning banner.
