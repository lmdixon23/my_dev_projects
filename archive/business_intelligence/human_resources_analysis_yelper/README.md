# Human Resources Analysis

## Overview

**Human_Resources_Analysis** is a Power BI report that surfaces headcount, attrition, compensation, and workforce-diversity metrics for the bundled "Yelper" sample dataset. It demonstrates a standard people-analytics dashboard: KPI cards for headline workforce metrics, an attrition decomposition, a comp-band distribution, and a drill-through to a single-department profile.

## Key Features

- **Headline KPIs**: Active Headcount, YTD Attrition %, Avg Tenure, Time-to-Fill, Total Comp Spend.
- **Headcount Trend**: Monthly headcount movement with hires, terminations, and net change.
- **Attrition Analysis**: Voluntary vs. involuntary, by department, manager, tenure band, and performance rating.
- **Compensation Distribution**: Comp bands by job family, with median / quartile markers and pay-equity slicers.
- **Diversity Slicers**: Gender, ethnicity, age band, location — all cross-filter every visual on the page.
- **Drill-Through**: Click any department to jump to a single-department profile (org chart, attrition trend, open reqs).

## Architecture

Star-schema model: `FactEmployeeSnapshot` plus dimensions for `DimEmployee`, `DimDepartment`, `DimDate`, `DimJobFamily`. Measures are organized in a dedicated `__Measures` table by convention.

```
human_resources_analysis_yelper.pbix    Power BI report (.pbix)
human_resources_analysis_yelper.xlsx    Source data workbook (loaded by the report)
README.md
```

## Example Usage

After opening the report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The report loads the `.xlsx` source and applies all relationships.
- **Filter**: Use the date / department / location slicers at the top of each page.
- **Drill**: Right-click a department in the headcount matrix and choose `Drill through -> Department Profile` to see that team's detail.
- **Export**: `File -> Export -> Export to PDF` produces a stakeholder-ready handout.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/human_resources_analysis_yelper
```

### Running

Open `human_resources_analysis_yelper.pbix` in Power BI Desktop and click `Home -> Refresh`.

### Testing

Manual smoke check (see the parent `business_intelligence/README.md` for the standard four-step procedure).

## Technical Specifications

- **Tool**: Power BI Desktop
- **Data model**: star-schema; one fact table, four dimensions
- **Measures**: DAX, organized in a dedicated `__Measures` table
- **Sample data**: bundled `.xlsx`, no external connection required

## What This Project Demonstrates

- A standard **people-analytics dashboard pattern** (KPI -> headcount trend -> attrition -> comp distribution -> drill-through) executed cleanly.
- **Star-schema discipline** with an explicit measures table — the maintainability convention Power BI teams converge on at scale.
- **Self-contained reproducibility**: a reviewer can open the file and explore it without provisioning an HRIS.

## Scope

- The dataset is synthetic; the *insights* are illustrative.
- No row-level security applied — every viewer sees every employee record, including comp. In a real HR deployment RLS is mandatory.
- Drill-through depth is one level; in a real deployment you'd want multi-hop (department -> manager -> employee).
- No PII masking on the sample data — fine for a demo, not for a production HR rollout.

## Future Enhancements

1. **Predictive Attrition**: Add an AzureML / Python flight-risk score and surface it as a column on the employee profile.
2. **Pay-Equity / Distribution View**: Add compensation-distribution and pay-gap measures across role, level, and tenure — a high-value HR-analytics lens absent from the current build.
3. **Row-Level Security**: Add RLS so managers see only their own org and HRBPs see only their assigned departments. (Especially load-bearing here given the unmasked comp data noted in Scope.)
4. **Service Deployment**: Push to the Power BI Service with scheduled refresh and a paginated comp-review export.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
