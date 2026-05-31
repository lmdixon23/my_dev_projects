# Competitive Marketing Analysis

## Overview

**Competitive_Marketing_Analysis** is a Power BI report that benchmarks a brand against its competitive set across share-of-voice, share-of-search, channel mix, and campaign spend. It demonstrates a standard competitive-intelligence dashboard: KPI cards for headline share metrics, a competitor-matrix page, a trend / momentum view, and a drill-through to a single-competitor profile.

## Key Features

- **Headline KPIs**: Share of Voice, Share of Search, Estimated Spend, Brand Sentiment, Campaign Count.
- **Competitor Matrix**: Brands crossed with channel (paid search, social, display, organic, PR) and geography.
- **Momentum View**: Period-over-period change in share, ranking gains/losses, and notable campaign launches.
- **Drill-Through**: Click any competitor in the matrix to jump to a single-competitor profile page (channel mix, top creatives, share trend).
- **Slicers**: Date, geography, channel, brand segment — all cross-filter every visual on the page.

## Architecture

Star-schema model: `FactCompetitiveActivity` plus dimensions for `DimBrand`, `DimChannel`, `DimDate`, `DimGeography`. Measures are organized in a dedicated `__Measures` table by convention. Source data is pulled from public web sources (or staged inside the `.pbix` itself) — no bundled `.xlsx` workbook is shipped with this report.

```
competitive_marketing_analysis.pbix    Power BI report (.pbix)
README.md
```

## Example Usage

After opening the report in Power BI Desktop, you can observe the following sequence of operations:

- **Load**: The report loads its embedded / web-sourced data and applies all relationships.
- **Filter**: Use the date / geography / channel slicers at the top of each page.
- **Drill**: Right-click a competitor in the matrix and choose `Drill through -> Competitor Profile` to see that brand's activity.
- **Export**: `File -> Export -> Export to PDF` produces a stakeholder-ready handout.

## Getting Started

### Prerequisites

- **Power BI Desktop** (Windows). Download free from [Microsoft](https://powerbi.microsoft.com/en-us/desktop/).

### Installation

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/business_intelligence/competitive_marketing_analysis
```

### Running

Open `competitive_marketing_analysis.pbix` in Power BI Desktop and click `Home -> Refresh`.

### Testing

Manual smoke check (see the parent `business_intelligence/README.md` for the standard four-step procedure).

## Technical Specifications

- **Tool**: Power BI Desktop
- **Data model**: star-schema; one fact table, four dimensions
- **Measures**: DAX, organized in a dedicated `__Measures` table
- **Sample data**: embedded in the `.pbix` (or sourced from public web endpoints); no external workbook required

## What This Project Demonstrates

- A standard **competitive-intelligence dashboard pattern** (KPI -> matrix -> momentum -> drill-through) executed cleanly.
- **Star-schema discipline** with an explicit measures table — the maintainability convention Power BI teams converge on at scale.
- **Self-contained reproducibility**: a reviewer can open the file and explore it without provisioning a database or licensing a third-party data feed.

## Scope

- The dataset is synthetic / illustrative; the *insights* are directional, not authoritative.
- Share-of-voice and spend estimates in production typically require a paid data provider (Similarweb, SEMrush, Pathmatics, etc.) — this report demonstrates the *shape* of the dashboard, not a live feed.
- No row-level security applied — every viewer sees every brand.
- Drill-through depth is one level; in a real deployment you'd want multi-hop (brand -> campaign -> creative).

## Future Enhancements

1. **Normalized Share-of-Voice Index**: Add a category-indexed SoV measure (each brand's SoV relative to the category mean) so momentum is comparable across categories of different sizes — a deeper analytical cut than the raw momentum view.
2. **Sentiment Overlay**: Add a social-listening feed (Brandwatch / Talkwalker) and overlay sentiment on the momentum view.
3. **Live Data Feed**: Wire the report to a paid competitive-intelligence API for real share-of-voice numbers.
4. **Service Deployment**: Push to the Power BI Service with scheduled refresh.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License.

## Contact

For further inquiries or collaboration opportunities, please contact lmdixon23@gmail.com.
