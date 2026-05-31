# Customer Profitability Analysis

## Overview

**Customer_Profitability_Analysis** is a Power BI report that breaks down per-customer revenue, cost-to-serve, and margin for the bundled "Yelper" sample dataset. It demonstrates a standard finance / sales-ops dashboard: KPI cards for headline metrics, a customer-segmentation matrix, a margin-waterfall page, and a drill-through to a single-customer profile.

## Key Features

- **Headline KPIs**: Revenue, Gross Profit, Margin %, Customer Count, Avg Customer Value.
- **Segmentation Matrix**: Customers crossed with product line / region / acquisition channel.
- **Margin Waterfall**: Period-over-period decomposition of margin movement into volume, mix, and price effects.
- **Drill-Through**: Click any customer in the matrix to jump to a single-customer profile page (purchase history, top products, margin trend).
- **Slicers**: Date, region, channel, customer segment — all cross-filter every visual on the page.

## Architecture

Star-schema model: `FactSales` plus dimensions for `DimCustomer`, `DimProduct`, `DimDate`, `DimChannel`. Measures are organized in a dedicated `__Measures` table by convention.

```
customer_profitability_analysis_yelper.pbix    Power BI report (.pbix)
customer_profitability_analysis_yelper.xlsx    Source data workbook (loaded by the report)
README.md
```

## Example Usage

After opening the report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The report loads the `.xlsx` source and applies all relationships.
- **Filter**: Use the date / region / channel slicers at the top of each page.
- **Drill**: Right-click a customer in the segmentation matrix and choose `Drill through -> Customer Profile` to see that customer's history.
- **Export**: `File -> Export -> Export to PDF` produces a stakeholder-ready handout.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/customer_profitability_analysis
```

### Running

Open `customer_profitability_analysis_yelper.pbix` in Power BI Desktop and click `Home -> Refresh`.

### Testing

Manual smoke check (see the parent `business_intelligence/README.md` for the standard four-step procedure).

## Technical Specifications

- **Tool**: Power BI Desktop
- **Data model**: star-schema; one fact table, four dimensions
- **Measures**: DAX, organized in a dedicated `__Measures` table
- **Sample data**: bundled `.xlsx`, no external connection required

## What This Project Demonstrates

- A standard **finance dashboard pattern** (KPI -> segmentation -> waterfall -> drill-through) executed cleanly.
- **Star-schema discipline** with an explicit measures table — the maintainability convention Power BI teams converge on at scale.
- **Self-contained reproducibility**: a reviewer can open the file and explore it without provisioning a database.

## Scope

- The dataset is synthetic; the *insights* are illustrative.
- No row-level security applied — every viewer sees every customer.
- Drill-through depth is one level; in a real deployment you'd want multi-hop (customer -> order -> line item).

## Future Enhancements

1. **Cost-to-Serve / Activity-Based Margin**: Allocate service costs (support, shipping, returns) per customer so the report shows *net* profitability, not just gross margin. This is the central analytical concept of customer profitability and the dashboard's biggest current gap.
2. **What-If Parameters**: Add a price-discount slider that recomputes margin in real time.
3. **Row-Level Security**: Add RLS so account managers see only their own book.
4. **Service Deployment**: Push to the Power BI Service with scheduled refresh.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
