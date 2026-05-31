# Procurement Analysis

## Overview

**Procurement_Analysis** is a Power BI report that breaks down spend by category, supplier concentration, and purchase-order velocity for the bundled "Yelper" sample dataset. It demonstrates a standard procurement / sourcing dashboard: KPI cards for headline spend metrics, a category-and-supplier matrix, a concentration view, and a drill-through to a single-supplier profile.

## Key Features

- **Headline KPIs**: Total Spend, PO Count, Avg PO Value, Active Supplier Count, % Spend Under Contract.
- **Spend-by-Category Matrix**: Category and sub-category crossed with cost center and region.
- **Supplier Concentration**: Pareto chart of suppliers by spend, with top-N / tail thresholds and single-source flags.
- **Spend Trend**: Period-over-period decomposition into price vs. volume, plus maverick-spend callouts.
- **Drill-Through**: Click any supplier in the matrix to jump to a single-supplier profile page (PO history, contract status, top categories).
- **Slicers**: Date, category, cost center, region, contract status — all cross-filter every visual on the page.

## Architecture

Star-schema model: `FactPurchaseOrders` plus dimensions for `DimSupplier`, `DimCategory`, `DimDate`, `DimCostCenter`. Measures are organized in a dedicated `__Measures` table by convention.

```
procurement_analysis_yelper.pbix    Power BI report (.pbix)
procurement_analysis_yelper.xlsx    Source data workbook (loaded by the report)
README.md
```

## Example Usage

After opening the report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The report loads the `.xlsx` source and applies all relationships.
- **Filter**: Use the date / category / cost-center slicers at the top of each page.
- **Drill**: Right-click a supplier in the concentration view and choose `Drill through -> Supplier Profile` to see that supplier's history.
- **Export**: `File -> Export -> Export to PDF` produces a stakeholder-ready handout.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/procurement_analysis_yelper
```

### Running

Open `procurement_analysis_yelper.pbix` in Power BI Desktop and click `Home -> Refresh`.

### Testing

Manual smoke check (see the parent `business_intelligence/README.md` for the standard four-step procedure).

## Technical Specifications

- **Tool**: Power BI Desktop
- **Data model**: star-schema; one fact table, four dimensions
- **Measures**: DAX, organized in a dedicated `__Measures` table
- **Sample data**: bundled `.xlsx`, no external connection required

## What This Project Demonstrates

- A standard **procurement dashboard pattern** (KPI -> category matrix -> supplier concentration -> drill-through) executed cleanly.
- **Star-schema discipline** with an explicit measures table — the maintainability convention Power BI teams converge on at scale.
- **Self-contained reproducibility**: a reviewer can open the file and explore it without provisioning an ERP connection.

## Scope

- The dataset is synthetic; the *insights* are illustrative.
- No row-level security applied — every viewer sees every supplier and every PO. In a real deployment category managers would be scoped to their own categories.
- Maverick-spend detection is rule-based (off-contract flag); a production setup would tie back to a contract repository.
- Drill-through depth is one level; in a real deployment you'd want multi-hop (supplier -> PO -> line item -> GL posting).

## Future Enhancements

1. **Savings Tracker**: Add a negotiated-vs-realized savings page tied to contract effective dates.
2. **Supplier Concentration / Tail-Spend (Pareto)**: Add an 80/20 spend-concentration view and a tail-spend page — the standard procurement lens for consolidation opportunities, not currently present.
3. **Row-Level Security**: Add RLS scoped by category manager and cost-center owner.
4. **Service Deployment**: Push to the Power BI Service with scheduled refresh and email-subscription delivery to category managers.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
