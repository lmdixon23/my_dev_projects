# Supplier Quality Analysis

## Overview

**Supplier_Quality_Analysis** is a Power BI report that monitors supplier defect rates, on-time delivery, and a composite supplier scorecard for the bundled "Yelper" sample dataset. It demonstrates a standard supply-chain quality dashboard: KPI cards for headline quality metrics, a defect-by-material matrix, a delivery-performance view, and a drill-through to a single-supplier profile.

## Key Features

- **Headline KPIs**: Defect Rate (PPM), On-Time Delivery %, First-Pass Yield, Total Downtime (min), Supplier Scorecard Score.
- **Defect Matrix**: Suppliers crossed with material, plant, and defect type.
- **Delivery Performance**: On-time vs. late vs. early, with lead-time variance and aging of open POs.
- **Supplier Scorecard**: Composite score (quality, delivery, cost, responsiveness) with tier banding and trend arrows.
- **Drill-Through**: Click any supplier in the scorecard to jump to a single-supplier profile page (defect trend, delivery history, top materials, open NCRs).
- **Slicers**: Date, plant, material category, supplier tier — all cross-filter every visual on the page.

## Architecture

Star-schema model: `FactInspection` and `FactDelivery` plus dimensions for `DimSupplier`, `DimMaterial`, `DimDate`, `DimPlant`. Measures are organized in a dedicated `__Measures` table by convention.

```
supplier_quality_analysis_yelper.pbix    Power BI report (.pbix)
supplier_quality_analysis_yelper.xlsx    Source data workbook (loaded by the report)
README.md
```

## Example Usage

After opening the report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The report loads the `.xlsx` source and applies all relationships.
- **Filter**: Use the date / plant / material slicers at the top of each page.
- **Drill**: Right-click a supplier in the scorecard and choose `Drill through -> Supplier Profile` to see that supplier's quality history.
- **Export**: `File -> Export -> Export to PDF` produces a stakeholder-ready handout.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/supplier_quality_analysis_yelper
```

### Running

Open `supplier_quality_analysis_yelper.pbix` in Power BI Desktop and click `Home -> Refresh`.

### Testing

Manual smoke check (see the parent `business_intelligence/README.md` for the standard four-step procedure).

## Technical Specifications

- **Tool**: Power BI Desktop
- **Data model**: star-schema; two fact tables, four dimensions
- **Measures**: DAX, organized in a dedicated `__Measures` table
- **Sample data**: bundled `.xlsx`, no external connection required

## What This Project Demonstrates

- A standard **supplier-quality dashboard pattern** (KPI -> defect matrix -> delivery -> scorecard -> drill-through) executed cleanly.
- **Star-schema discipline** with an explicit measures table — the maintainability convention Power BI teams converge on at scale.
- **Self-contained reproducibility**: a reviewer can open the file and explore it without provisioning an ERP / QMS connection.

## Scope

- The dataset is synthetic; the *insights* are illustrative.
- No row-level security applied — every viewer sees every supplier. In a real deployment commodity managers would be scoped to their own categories.
- The composite scorecard weights (quality / delivery / cost / responsiveness) are hard-coded — a production setup would expose them as parameters governed by the sourcing org.
- Drill-through depth is one level; in a real deployment you'd want multi-hop (supplier -> shipment -> inspection lot -> defect record).

## Future Enhancements

1. **NCR Workflow Integration**: Embed open non-conformance reports from the QMS so the supplier profile becomes the single pane of glass.
2. **SPC Control Chart**: Add a statistical-process-control chart (defect-rate mean ± σ-limits) on the defect trend so out-of-control suppliers are flagged by rule, not eyeballing — the quality-engineering lens this dashboard is built for.
3. **Row-Level Security**: Add RLS scoped by commodity manager and plant.
4. **Service Deployment**: Push to the Power BI Service with scheduled refresh and a monthly supplier-scorecard email subscription.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
