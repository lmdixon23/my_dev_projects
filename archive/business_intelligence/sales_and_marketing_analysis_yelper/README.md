# Sales and Marketing Analysis

## Overview

**Sales_and_Marketing_Analysis** is a Power BI report that ties marketing campaign activity to sales pipeline and closed revenue for the bundled "Yelper" sample dataset. It demonstrates a standard revenue-operations dashboard: KPI cards for headline funnel metrics, a campaign-attribution matrix, a pipeline-stage view, and a drill-through to a single-campaign profile.

## Key Features

- **Headline KPIs**: Pipeline Value, Closed-Won Revenue, Win Rate, Avg Deal Size, MQL-to-SQL Conversion, CAC.
- **Funnel View**: Lead -> MQL -> SQL -> Opportunity -> Closed-Won, with stage-conversion and velocity metrics.
- **Campaign Attribution**: Campaigns crossed with channel, segment, and region; first-touch and multi-touch views.
- **Pipeline Health**: Stage aging, slipped close dates, single-threaded deals, coverage ratio vs. quota.
- **Drill-Through**: Click any campaign in the attribution matrix to jump to a single-campaign profile (spend, leads, sourced pipeline, ROI).
- **Slicers**: Date, channel, segment, region, rep — all cross-filter every visual on the page.

## Architecture

Star-schema model: `FactOpportunity` and `FactCampaignTouch` plus dimensions for `DimCampaign`, `DimAccount`, `DimDate`, `DimChannel`. Measures are organized in a dedicated `__Measures` table by convention.

```
sales_and_marketing_analysis_yelper.pbix    Power BI report (.pbix)
sales_and_marketing_analysis_yelper.xlsx    Source data workbook (loaded by the report)
README.md
```

## Example Usage

After opening the report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The report loads the `.xlsx` source and applies all relationships.
- **Filter**: Use the date / channel / segment slicers at the top of each page.
- **Drill**: Right-click a campaign in the attribution matrix and choose `Drill through -> Campaign Profile` to see that campaign's detail.
- **Export**: `File -> Export -> Export to PDF` produces a stakeholder-ready handout.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/sales_and_marketing_analysis_yelper
```

### Running

Open `sales_and_marketing_analysis_yelper.pbix` in Power BI Desktop and click `Home -> Refresh`.

### Testing

Manual smoke check (see the parent `business_intelligence/README.md` for the standard four-step procedure).

## Technical Specifications

- **Tool**: Power BI Desktop
- **Data model**: star-schema; two fact tables, four dimensions
- **Measures**: DAX, organized in a dedicated `__Measures` table
- **Sample data**: bundled `.xlsx`, no external connection required

## What This Project Demonstrates

- A standard **revenue-operations dashboard pattern** (KPI -> funnel -> attribution -> pipeline health -> drill-through) executed cleanly.
- **Star-schema discipline** with an explicit measures table — the maintainability convention Power BI teams converge on at scale.
- **Self-contained reproducibility**: a reviewer can open the file and explore it without provisioning a CRM or marketing-automation connection.

## Scope

- The dataset is synthetic; the *insights* are illustrative.
- No row-level security applied — every viewer sees every rep's pipeline. In a real deployment reps would see only their own book and managers their team's.
- Multi-touch attribution is a simple position-based model (40/20/40); a production setup would typically use a vendor model or a fitted algorithmic model.
- Drill-through depth is one level; in a real deployment you'd want multi-hop (campaign -> lead -> opportunity -> activity).

## Future Enhancements

1. **Algorithmic Attribution**: Replace the position-based weighting with a fitted Markov or Shapley model.
2. **Cohort Retention / CAC-Payback**: Add an acquisition-cohort retention view and a CAC-payback measure, connecting marketing spend to retained revenue rather than first-touch conversion only.
3. **Row-Level Security**: Add RLS scoped by rep and manager hierarchy.
4. **Service Deployment**: Push to the Power BI Service with scheduled refresh and a weekly pipeline-review email subscription.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
