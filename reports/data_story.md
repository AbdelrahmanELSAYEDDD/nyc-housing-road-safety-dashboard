
### The question
Do New York City areas that produce more affordable housing also have more serious traffic crashes per resident — and how does this differ by place, year, construction type and income group? Affordable homes are built or preserved to house people for decades. If they are concentrated where streets are most dangerous, housing and road-safety programmes could benefit from being planned together.

### The data
* **Housing:** HPD's *Affordable Housing Production by Building* (H2) — 9,551 building records, of which 716 buildings completed in 2022–2025 are confidential and cannot be placed on a map.
* **Transportation:** DOT's *Serious Injury Response, Tracking & Analysis Program* (SIRTA) — 13,309 serious crashes kept after removing 445 unusable or duplicate rows.
* **Geographic reference:** MODZCTA ZIP-code areas (boundaries and 2018 population), used only to place records and compute per-resident rates.
* Snapshot: 2026-10-16 (fresh-download). The partial year 2026 is excluded.

### How the datasets were connected
Both datasets were aggregated to **ZIP-code area × year** (177 areas × 4 years = 708 rows) and joined one-to-one, so no record was duplicated. Records were placed in areas by their coordinates first and by ZIP code otherwise; 5.2–12.4% of each year's crashes could not be placed and are kept in borough totals only.

### What we found
* **RQ1 — association:** across 177 areas, units completed per resident and the serious-crash rate show a moderate positive association (Spearman ρ = 0.33).
* **RQ2 — overlap:** 44 areas combine relatively high production with a relatively high crash rate (by borough: Brooklyn 15, Bronx 14, Manhattan 11, Queens 3, Staten Island 1).
* **RQ3 — change over time:** from 2022 to 2025, local serious crashes changed by +21.6% in areas with no completions, +17.3% in lower-half areas, -2.2% in upper-half areas (citywide: +2.4%).
* **RQ4 — timing:** weekend share 27.9% in upper-tier areas vs 27.4% elsewhere; night share 29.4% vs 25.9% (exploratory).
* **RQ5 — construction type:** median crash rate 31.4 in new-construction-dominant areas vs 23.2 in preservation-dominant areas (a descriptive difference; the groups differ in borough mix).
* **RQ6 — income bands:** band values range from 27.9 to 42.4 serious crashes per 100,000 residents per year, compared with 29.3 for the average resident. These describe where units were built, not personal risk.
* **RQ7 — earlier similar serious injuries:** shares (known values only): No completions 4.5%; Lower half 4.9%; Upper half 8.4%.
* **RQ8 — screening list:** highest-scoring areas for further investigation: 11101, 10035, 10454, 10474, 11217 (not a prediction).

### What surprised us
One finding that stood out was the difference between new construction and preservation. Areas with more new-construction units per resident tended to have higher serious-crash rates (ρ = 0.42), while preservation showed a much weaker relationship (ρ = 0.10). We also found that new-construction-dominant areas had a higher median crash rate (31.4) than preservation-dominant areas (23.2). This is an interesting difference, but it does not mean that new construction causes more crashes.

### What the data cannot tell us
These are **area-level associations**: they do not show that housing production causes crashes, and they say nothing about the risk faced by individual residents. Preservation does not necessarily add residents. Rates use 2018 population estimates, four years are too few for trend claims, some crashes could not be placed in an area, and SIRTA covers serious crashes only.

### Why it matters for New York City
The results can help **DOT** and **HPD** see where affordable housing and serious crashes overlap, so that street-safety reviews can be considered alongside housing projects — especially in the RQ2 overlap areas and the RQ8 candidate areas, where unfinished projects will bring new or renovated homes. Community boards and housing advocates can use the website to look up their own borough, year and housing type. Any action should start with a closer local look, because these figures identify places to investigate, not causes.
