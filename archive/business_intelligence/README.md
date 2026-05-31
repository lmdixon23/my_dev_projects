# Power BI Reports

## Overview

**Power_BI** is a set of business intelligence reports built in Microsoft Power BI Desktop. Each subfolder contains a `.pbix` file (the report itself) and an `.xlsx` file (the underlying data model). The reports were authored against publicly available or synthetic / "Yelper" sample data and demonstrate end-to-end BI work: data modeling, DAX measures, visual design, and narrative-driven dashboards across six functional areas.

## Key Features

- **Six Domains Covered**: Competitive Marketing Analysis, Customer Profitability, Human Resources, Procurement, Retail, Sales & Marketing, and Supplier Quality.
- **Self-Contained Data**: Each report ships with its `.xlsx` source so reviewers can open the file in Power BI Desktop and refresh it without external connections.
- **Standard Power BI Patterns**: Star-schema data models, calculated columns vs measures used appropriately, drill-throughs, slicers, and KPI cards.

## Architecture

Each report is a self-contained `.pbix + .xlsx` pair in its own directory. No external data sources are required to open and refresh the reports in Power BI Desktop.

```
competitive_marketing_analysis/
    competitive_marketing_analysis.pbix
customer_profitability_analysis/
    customer_profitability_analysis_yelper.pbix
    customer_profitability_analysis_yelper.xlsx
human_resources_analysis_yelper/
    human_resources_analysis_yelper.pbix
    human_resources_analysis_yelper.xlsx
procurement_analysis_yelper/
    procurement_analysis_yelper.pbix
    procurement_analysis_yelper.xlsx
retail_analysis_yelper/
    retail_analysis_yelper.pbix
    retail_analysis_yelper.xlsx
sales_and_marketing_analysis_yelper/
    sales_and_marketing_analysis_yelper.pbix
    sales_and_marketing_analysis_yelper.xlsx
supplier_quality_analysis_yelper/
    supplier_quality_analysis_yelper.pbix
    supplier_quality_analysis_yelper.xlsx
The Data Analysis Process.png   Reference diagram used in the reports' narrative.
```

## Example Usage

After opening a report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The `.pbix` file opens; the data model loads from the bundled `.xlsx`.
- **Refresh**: "Refresh" re-loads any changes in the spreadsheet.
- **Explore**: Use slicers, drill-throughs, and bookmarks to explore each report's narrative pages.
- **Export**: Each report supports the standard Power BI export to PDF / PowerPoint for stakeholder distribution.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).
- **Microsoft Excel** or any spreadsheet tool that can read `.xlsx` (only needed if you want to modify the underlying data).

### Installation

Clone the repository and navigate to one of the report folders:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/<report_folder>
```

### Running

Open the `.pbix` file in Power BI Desktop, then click `Home -> Refresh` to load the data.

### Testing

No automated tests; review is visual. Recommended manual smoke check per report:

1. Open the `.pbix`. Confirm no broken visuals (red ⚠ icons).
2. Open Model view; confirm all relationships are active.
3. Open Data view; confirm every table has rows.
4. Click through each report page; interact with one slicer per page to verify cross-filtering still works.

## Reports in this directory

| Report | Domain | Notes |
|---|---|---|
| [Competitive Marketing Analysis](./competitive_marketing_analysis/) | Marketing | Competitor benchmarking and share-of-voice. |
| [Customer Profitability](./customer_profitability_analysis/) | Finance / sales | Per-customer margin breakdown. |
| [Human Resources](./human_resources_analysis_yelper/) | HR | Headcount, attrition, comp-band distribution. |
| [Procurement](./procurement_analysis_yelper/) | Operations | Spend by category, supplier concentration. |
| [Retail](./retail_analysis_yelper/) | Retail | Store-level revenue, basket size, foot traffic. |
| [Sales & Marketing](./sales_and_marketing_analysis_yelper/) | GTM | Pipeline + campaign attribution. |
| [Supplier Quality](./supplier_quality_analysis_yelper/) | Supply chain | Defect rates, on-time delivery. |

## Technical Specifications

- **Tool**: Power BI Desktop (latest)
- **Source data**: bundled `.xlsx` files (per report); no external connections required
- **Data modeling**: star-schema with explicit measure tables; DAX measures over calculated columns where appropriate
- **Sample data**: "Yelper" synthetic dataset commonly used in BI coursework

## What This Project Demonstrates

- **Domain breadth**: BI work across seven functional areas of a business — useful signal for "BI-as-platform" roles where a single analyst supports multiple departments.
- **Self-contained reproducibility**: bundling the data alongside the report (instead of relying on a private SQL Server connection) means a reviewer can actually open and explore the work — the single highest barrier to "I tried to look at your portfolio."
- **Standard BI hygiene**: explicit measure tables, named patterns for time intelligence, drill-throughs that follow Power BI design-guide conventions.

## Scope

- These reports are built on sample / synthetic data; the *insights* are illustrative, not real business findings.
- No automated regression tests on DAX (Power BI has limited tooling for this); the manual smoke check above is the recommended substitute.
- Reports were authored against a specific Power BI Desktop release; newer releases occasionally change visual rendering. Re-save after opening if you intend to publish.

## Future Enhancements

These are ordered to lead with what distinguishes this BI portfolio from a folder of `.pbix` files — source control and CI — followed by the deployment/security items.

1. **Test Harness**: Use `pbi-tools` to export each report to source-controllable text and add CI snapshot diffing.
2. **Tabular Editor Templates**: Manage measures in source-controllable `.bim` files via Tabular Editor for proper versioning.
3. **Power BI Service Deployment**: Push each `.pbix` to a Power BI workspace with scheduled refresh.
4. **Row-Level Security**: Add RLS roles so each report only shows a manager their own team's data (per-report specifics are in each project's own enhancement list).

## Contributing

Contributions are welcome. Open an issue first if you're planning a substantial change so we can align on scope.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
