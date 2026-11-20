# Financial Customer Complaint Analytics

**Tekloomy internship project | Excel • SQL • Power BI • Data quality • KPI analysis**

## Project overview

This project analyses a supplied financial-customer-complaint dataset to understand complaint volumes, unresolved backlog, issue concentration, product/company/channel patterns, geography, and response timeliness. The workflow combines data inspection and cleaning, SQL-style reporting aggregates, KPI validation, and an interactive two-page Power BI report.

The analysis is based on the supplied `lecture-file.csv` training/project file. It is **not** evidence about actual named financial institutions, a regulatory finding, or a representative estimate of the wider financial-services industry. The source file does not include a data-provenance statement or sampling methodology.

## Validated headline results

| Measure | Result | Definition |
|---|---:|---|
| Raw rows | 5,000 | Rows in the supplied CSV |
| Exact duplicate rows removed | 25 | Duplicate `complaint_id` groups were checked for conflicting values before removal |
| Unique complaints | **4,975** | One record per unique complaint ID |
| Open complaints | **310** | `response_status = Open` |
| Closed complaints | **4,665** | `response_status = Closed` |
| Open complaint rate | **6.23%** | 310 / 4,975 |
| On-time closed responses | **4,202 (90.08%)** | Timely response flag validated against response and due dates |
| Late closed responses | **463 (9.92%)** | Late response flag validated against response and due dates |
| Open cases at least 90 days overdue | **240 (77.4% of open cases)** | Age measured as of 20 November 2026 |
| Average overdue age of open cases | **205.3 days** | As of 20 November 2026 |
| Maximum overdue age | **394 days** | As of 20 November 2026 |
| Average closed response time | **8.76 days** | `date_company_responded - date_received` |

### Key operational findings

- **Aged backlog is the most material control concern.** All 310 open cases are beyond the supplied due date as of 20 November 2026; 240 have been overdue for at least 90 days.
- **Fee/billing themes dominate the largest issue groups.** Unexpected Fees (35), Billing Dispute (25), and Account Access (23) are the top three categories, together representing 83 cases (26.8% of the open backlog). Interest Charges contributes a further 18.
- **Phone is the first channel to investigate.** It has 130 late closed responses among 1,168 closed Phone cases, an 11.13% late rate—the highest among the four channels. A high count alone is not enough; the rate uses the channel's closed-case denominator.
- **Buy Now, Pay Later has the highest product-level open rate.** It has 33 open cases among 350 complaints (9.43%). Credit Card has the highest absolute open count (73), so count and rate tell different stories.
- **The final month is partial.** October 2026 contains data through 15 October only (212 records), so it must not be compared directly with full months.

## Project workflow

1. **Understand the dataset:** profile the 14 source fields, business labels, dates, response status, and missing values.
2. **Clean and validate:** remove exact duplicate complaint IDs only after checking duplicate groups for conflicting rows; trim whitespace; standardise case and display labels; parse date fields; preserve missing state values as Unknown rather than inventing geography.
3. **Analyse and calculate KPIs:** calculate complaint totals, open/closed split, response timeliness, overdue ageing, issue/category concentration, product open rates, channel response rates, and monthly intake.
4. **Build reporting outputs:** use grouped reporting views/aggregates for company, product, issue, state, channel, and month.
5. **Visualise:** build two Power BI report pages—Executive Overview and Operational Analysis—with seven KPI cards, six analytical visuals, and slicers for company, product, state, and month.
6. **Recommend improvements:** translate the measured patterns into targeted process reviews, a backlog recovery plan, and channel/product monitoring.

## Reproduce the cleaning and validation

Requirements: Python 3.10+ and pandas (see `requirements.txt`). From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py scripts\clean_validate.py --input data\raw\lecture-file.csv --output data\processed\complaints_cleaned.csv --as-of-date 2026-11-20
```

The script writes the cleaned CSV and `validation_summary.json`. It stops if duplicate IDs contain conflicting records, required dates fail parsing, the date-rule validation fails, or the headline KPI reconciliation does not match.

## Power BI report

The report design has two pages:

- **Executive Overview:** headline KPIs, monthly complaint intake trend, and Company/Product/State/Month slicers.
- **Operational Analysis:** company, product, issue category, state, and response-channel analysis, with Company/Product/State slicers.

The PBIX is not included in this public starter repository by default because a PBIX can embed the underlying dataset. Keep the PBIX in `powerbi/` locally and share it separately through the internship portal unless you have permission to publish the embedded data. `powerbi/README.md` explains how to add it.

## SQL artefacts

The project workflow used reporting objects named:

- `VW_COMPANY_BACKLOG_PERFORMANCE`
- `VW_PRODUCT_BACKLOG_PERFORMANCE`
- `VW_ISSUE_BACKLOG_PERFORMANCE`
- `VW_STATE_RESPONSE_PERFORMANCE`
- `VW_CHANNEL_RESPONSE_PERFORMANCE`
- `VW_MONTHLY_COMPLAINT_TRENDS`

The original executed SQL scripts were not available in the files used to assemble this repository. They are **not fabricated here**. Add the original scripts to `sql/` if you have them; until then, the independent CSV validation script is the reproducible calculation artefact.

## Recommendations

1. Review fee, billing, and interest-charge cases at case level; map root causes to fee rules, disclosures, transaction events, and billing controls. Proposed target: reduce the combined monthly volume of the top three issue categories by 20% within six months from a verified baseline.
2. Launch an aged-backlog recovery programme with named owners, next actions, customer updates, and escalation dates. Proposed target: reduce the 90+ day open backlog from 240 to 120 or fewer within 90 days, without closing cases merely to improve a metric.
3. Investigate Phone queue staffing, routing, callbacks, case complexity, and after-call work; separately review BNPL open cases. Proposed target: improve Phone on-time performance from 88.87% to at least 95% within 90 days, subject to management approval and operational feasibility.

## Limitations and responsible interpretation

- The source file has no provenance statement or sampling design; results describe this file only.
- Complaint categories are signals for investigation, not proof that an allegation is correct or that a law was violated.
- There is no customer identifier, so repeat complainant behaviour cannot be measured.
- Forty-nine records (0.98%) have missing state values; one open case has no state. Keep these as Unknown.
- The October 2026 month is partial.
- Ageing metrics use the fixed reporting date 20 November 2026 and must be recalculated when the report is refreshed.
- Exact original SQL scripts and the final PBIX were not available for independent source-code/model review when this repository package was assembled.

## Files

```text
.
├── README.md
├── PROJECT_DESCRIPTION.md       # copy into the internship portal (under 8,000 words)
├── REFERENCES.md                # authoritative complaint/data/Power BI guidance
├── requirements.txt
├── data/
│   ├── raw/                      # source CSV retained locally; ignored by Git
│   └── processed/                # cleaned CSV ignored; validation JSON tracked
├── docs/                         # report figures and supplementary notes
├── powerbi/                      # PBIX kept local by default; see README
├── report/                       # final internship report (.docx)
├── scripts/clean_validate.py
└── sql/README.md                 # notes on original SQL artefacts
```

## References

See [`REFERENCES.md`](REFERENCES.md) for the standards and official guidance used to frame the analysis.
