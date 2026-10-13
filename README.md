# Gleason Grade Group Mapper

A Python CLI and browser calculator for mapping pathologist-assigned prostate Gleason patterns to ISUP Grade Groups (1–5) and exploring localized prostate-cancer risk categories using PSA, clinical T stage and biopsy-core data.

**Clinical limitation:** This is an educational/research implementation, not a validated medical device or a substitute for pathology reporting, current clinical guidelines or multidisciplinary decisions. Histologic Grade Group by itself does **not** establish clinical risk. Risk categories may require data not present in the inputs. In particular, intermediate-risk subgroup classification is shown as *undetermined* without the positive-core fraction.

## Features

- Grade Groups for contemporary Gleason patterns 3–5, distinguishing 3+4 from 4+3.
- Higher third pattern in **needle biopsy** (included in the score) versus **prostatectomy** (retained separately for specialist review).
- Exploratory localized risk grouping by Grade Group, PSA, T stage and optional core fraction/PSA density.
- Browser single-case calculator and local CSV import/export in **web/index.html**.
- Python CLI for grade/risk assessment and CSV processing.
- Separate experimental supervisor/audit API in **agents/** and backend console in **web/operations.html**. Neither interprets images or grades histology.

The optional *Very Low Risk* label reflects a legacy category and requires PSA density and core criteria; newer guidelines may group such cases differently. The grade-only result's **risk_category** field is retained for backward compatibility and is not a comprehensive risk category. Use the risk assessment function with clinical parameters for an exploratory estimate.

## Browser use

Open **web/index.html** locally in a modern browser. Select the patterns and specimen type, enter clinical parameters, then select **Calculate grade and risk**. For batch use, choose a CSV with the required columns:

    primary_pattern,secondary_pattern,psa,t_stage

Optional columns: tertiary_pattern, specimen_type, num_positive_cores, total_cores, max_percent_per_core, psa_density.

The web application has no external scripts or API calls. Input files and calculations remain in the browser until you explicitly download the CSV. It needs no Python server or Pyodide. GitHub Actions includes a Pages publishing workflow; a public live URL is not claimed until deployment is verified.

## Python usage

Python 3.10–3.12 is tested in CI.

~~~bash
python -m pip install -r requirements.txt
python cli.py grade --primary 3 --secondary 4
python cli.py grade --primary 3 --secondary 4 --tertiary 5 --specimen-type biopsy
python cli.py risk --grade-group 2 --psa 8 --t-stage T1c --positive-cores 2 --total-cores 12
python cli.py assess --primary 4 --secondary 3 --psa 15 --t-stage T2b
python cli.py batch -i sample.csv -o results.csv
python -m pytest -q
node tests/browser_smoke.cjs
~~~

The browser and Python calculators use corresponding rules. Python batch processing rejects missing headers, invalid rows and inconsistent biopsy counts rather than assuming clinical values. CSV exports escape spreadsheet-formula-like content.

## Optional backend audit console

The **agents/** package provides a separate, generic demonstration of threshold checking and signed audit records, not Gleason scoring.

~~~bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py serve --host 127.0.0.1 --port 8000
~~~

Visit **http://127.0.0.1:8000/docs** for the generated API schema. **web/operations.html** requires a running compatible API at the same origin; GitHub Pages cannot host FastAPI.

The HMAC-SHA256 audit chain is in memory, not durable storage. Without a configured key, an ephemeral key is generated. The regex-based identifier screen catches selected common formats but does not establish de-identification or HIPAA compliance. Do not submit identifiable clinical records to the demo API. Its chat is a mock, not a medical reasoning service.

## Methods and references

- [ISUP 2019 consensus grading](https://pmc.ncbi.nlm.nih.gov/articles/PMC7382533/)
- [EAU classification and staging](https://uroweb.org/guidelines/prostate-cancer/chapter/classification-and-staging-systems)

Risk stratification is an **approximate implementation** for localized disease: independently verify definitions, thresholds and treatment decisions against the guideline edition used. The legacy Python treatment-option strings are illustrative, not patient-specific recommendations.

## Technology and license

Python standard library for core grading/CSV, FastAPI/Pydantic/Uvicorn for optional audit API, Pytest for testing, and plain HTML/CSS/JavaScript for the browser UI. Intended for current Chrome, Firefox, Safari and Edge; automated JavaScript tests run in Node, not a cross-browser lab.

[MIT License](LICENSE).
