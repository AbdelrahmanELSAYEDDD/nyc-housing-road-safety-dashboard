# Individual contributions and AI use

**Project:** Affordable Housing Development and Road Safety in New York City  
**Course:** Data Engineering and Visualization — Winter Semester 2026, German International University (GIU)  
**Student:** Abdelrahman Elsayed — **13004550**

## 1. Responsible student

The work has been developed through my decisions, instructions, review, Google Colab execution, debugging feedback, and verification, with assistance from ChatGPT.

## 2. My contributions, step by step

| Stage | What I did | Result / evidence |
|---|---|---|
| 1. Understand the assignment | Reviewed the GIU Project Description and asked ChatGPT to help explain the deliverables, required datasets, data cleaning, research questions, website, and submission steps. | Requirements organized into an implementation plan. |
| 2. Compare dataset options | Asked for help choosing a practical, efficient Housing & Development / Transportation dataset combination, taking available variables, cleaning effort, and integration feasibility into account. Reviewed the recommendations. | Selected H2 Affordable Housing Production by Building and T4 SIRTA. |
| 3. Decide the scope | Chose a manageable project using 2022–2025 data, eight research questions, Plotly charts, and a Dash website. Requested that unnecessary advanced statistics be removed. | A simplified implementation aligned with the course PDF. |
| 4. Plan the integration | Reviewed the decision to aggregate housing and crash records by geographic area and year instead of joining individual records directly. | MODZCTA × year integration, with the geographic file serving as a reference. |
| 5. Run and inspect data | Opened notebooks in Google Colab, ran real NYC Open Data downloads, and checked tables, plots, counts, and validation results. | Real-data execution and saved processed outputs. |
| 6. Test and improve the code | Reported notebook problems, including a pandas nullable-value (`pd.NA`) error, and used AI-assisted suggestions/revisions; reran and checked the affected work. | Iterative corrections and cleaner notebook explanations. |
| 7. Review findings | Checked the eight research figures, data-cleaning totals, source limitations, and numerical findings; asked for a comparison with the assignment PDF. | The analyses and supporting explanations were reviewed against the project scope. |
| 8. Request a focused correction | Reviewed a reported discrepancy involving crash records with missing boroughs and requested a minimal correction rather than a redesign. | The corrected borough summary includes 28 geographically derived Queens records and eight Unknown records. |
| 9. Verify revised outputs | Ran the simplified notebook and the revised version using real data in Colab and shared the processed-output archives for review. | 15 Oct: 74 PASS / 0 WARN / 0 FAIL; 16 Oct revised outputs: 76 PASS / 0 WARN / 0 FAIL. |
| 10. Prepare the website and repository | Requested the Dash application, reviewed upload structure, created a GitHub repository, and planned the final packaging and deployment workflow. | Website code prepared; correct repository upload and public deployment to be confirmed. |
| 11. Improve documentation | Requested simpler comments, natural explanations, a development history, an accurate AI-use log, and a clear explanation of my contribution. | Finalized contribution account and updated prompt log for review. |

These activities describe project direction, testing, review, and integration of AI assistance, not a claim of unaided software authorship. Research findings describe geographic associations, not proof that housing projects cause crashes.

## 3. How I used AI

I used **ChatGPT (OpenAI)** primarily to understand the assignment, compare datasets, plan the approach, diagnose and review issues, interpret notebook outputs, evaluate compliance, and prepare clear revision instructions.

I used **Claude (Anthropic)** for AI-assisted development and revision of Python notebook code, the data-processing and visualization functions, the Dash website source, and supporting project files. I supplied requirements and feedback, ran notebooks in Google Colab, and reviewed the outputs and changes. Details and the original available prompts are recorded in [`docs/AI_PROMPT_LOG.md`](docs/AI_PROMPT_LOG.md).

## 4. Testing and current status

| Item | Status |
|---|---|
| Simplified notebook, real-data run on 15 October 2026 | Completed: 80/80 code cells executed; 74 PASS; 0 WARN; 0 FAIL. |
| Revised data outputs from Colab on 16 October 2026 | Completed: 76 PASS; 0 WARN; 0 FAIL; all eight research summaries remained consistent. |
| Corrected borough summary | Verified in the revised outputs: 28 derived Queens records and eight Unknown; full totals reconcile. |
| Dashboard source | Rechecked with the final packaged files and the real data on 16 October 2026 (local test in a headless browser, run by Claude): the eight charts, five dropdowns, search and Generate Report work, and the results match the notebook. |
| Public website and GitHub repository | Final upload, URL, and end-to-end deployment verification still to be completed. |
| Final submission notebook | Executed in Colab with real data on 16 October 2026: 81/81 code cells; 76 PASS; 0 WARN; 0 FAIL. Checked during packaging: the saved notebook and its `processed_outputs.zip` come from the same run and their numbers match. |
