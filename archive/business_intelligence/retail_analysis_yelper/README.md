# Retail Analysis

## Overview

**Retail_Analysis** is a Power BI report that breaks down store-level revenue, basket size, foot traffic, and conversion for the bundled "Yelper" sample dataset. It demonstrates a standard retail-operations dashboard: KPI cards for headline store metrics, a store-performance matrix, a like-for-like trend view, and a drill-through to a single-store profile.

## Key Features

- **Headline KPIs**: Total Revenue, Transactions, Avg Basket Size, Foot Traffic, Conversion %, Sales per Sq Ft.
- **Store Matrix**: Stores crossed with region, store format, and product category.
- **Like-for-Like Trend**: Same-store revenue growth period-over-period, with new-store and closed-store callouts.
- **Basket Analysis**: Items per basket, units per transaction, and top product affinities.
- **Drill-Through**: Click any store in the matrix to jump to a single-store profile page (daily trend, category mix, staffing overlay).
- **Slicers**: Date, region, store format, category — all cross-filter every visual on the page.

## Architecture

Star-schema model: `FactTransactions` plus dimensions for `DimStore`, `DimProduct`, `DimDate`, `DimRegion`. Measures are organized in a dedicated `__Measures` table by convention.

```
retail_analysis_yelper.pbix    Power BI report (.pbix)
retail_analysis_yelper.xlsx    Source data workbook (loaded by the report)
README.md
```

## Example Usage

After opening the report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The report loads the `.xlsx` source and applies all relationships.
- **Filter**: Use the date / region / store-format slicers at the top of each page.
- **Drill**: Right-click a store in the matrix and choose `Drill through -> Store Profile` to see that store's detail.
- **Export**: `File -> Export -> Export to PDF` produces a stakeholder-ready handout.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/retail_analysis_yelper
```

### Running

Open `retail_analysis_yelper.pbix` in Power BI Desktop and click `Home -> Refresh`.

### Testing

Manual smoke check (see the parent `business_intelligence/README.md` for the standard four-step procedure).

## Technical Specifications

- **Tool**: Power BI Desktop
- **Data model**: star-schema; one fact table, four dimensions
- **Measures**: DAX, organized in a dedicated `__Measures` table
- **Sample data**: bundled `.xlsx`, no external connection required

## What This Project Demonstrates

- A standard **retail-operations dashboard pattern** (KPI -> store matrix -> like-for-like trend -> drill-through) executed cleanly.
- **Star-schema discipline** with an explicit measures table — the maintainability convention Power BI teams converge on at scale.
- **Self-contained reproducibility**: a reviewer can open the file and explore it without provisioning a POS connection.

## Scope

- The dataset is synthetic; the *insights* are illustrative.
- No row-level security applied — every viewer sees every store. In a real deployment district managers would be scoped to their own stores.
- Foot-traffic figures are sample / illustrative — a real deployment would tie to a door-counter or beacon feed.
- Drill-through depth is one level; in a real deployment you'd want multi-hop (store -> day -> transaction -> line item).

## Future Enhancements

1. **Inventory Overlay**: Join inventory on-hand to the store profile so out-of-stock can be correlated with lost sales.
2. **Basket Affinity / Market-Basket Lift**: Add a category-pair affinity view (lift between co-purchased categories) to surface cross-sell and planogram opportunities — a retail-specific analytical cut absent today.
3. **Row-Level Security**: Add RLS scoped by region and district manager.
4. **Service Deployment**: Push to the Power BI Service with scheduled refresh and a daily store-manager email subscription.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
