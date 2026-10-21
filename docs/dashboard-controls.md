# Dashboard design and controls

The four reports reuse their existing imported data, relationships, SQL outputs and DAX measures. The report layer has been redesigned without refreshing data or editing the existing model or DAX. Power BI Desktop can reserialize the model stream during a native save. Backups are in `backups/`.

## Start with the theme

Open a delivered PBIX in Power BI Desktop. Choose **View > Themes > Browse for themes**, then select that project's `themes/Light.json` or `themes/Dark.json`. The first four palette colors are chart accents. The next four are reserved for canvas, muted text, card surfaces and main text so both modes remain readable.

| Project | Chart colors | Navigation |
| --- | --- | --- |
| Customer Analytics | Purple `#7C3AED`, Pink `#EC4899`, Blue `#3B82F6`, Teal `#14B8A6` | Navy `#0F172A` |
| Loan Portfolio Analytics | Midnight `#0B132B`, Gold `#FBBF24`, Green `#22C55E`, Coral `#FB7185` | Navy `#0F172A` |
| Retail Demand Forecasting | Cyan `#06B6D4`, Emerald `#10B981`, Amber `#F59E0B`, Blue `#3B82F6` | Navy `#0F172A` |
| Zomato Restaurant Insights | Red `#E23744`, Teal `#008577`, Amber `#F59E0B`, Indigo `#6366F1` | Navy `#0F172A` |

Light surfaces: canvas `#F4F6FC`, cards `#FFFFFF`, text `#13223A`, muted text `#64748B`. Dark surfaces: canvas `#0B1120`, cards `#172036`, text `#E5EDF7`, muted text `#9AAEC7`. Green and red retain their semantic meaning; loan outcome charts describe observed resolved outcomes rather than an invented risk rating.

## Navigate and filter

Use the left navigation to switch analysis pages. In Desktop edit mode, use **Ctrl+click** on action buttons; normal clicks select the button for editing. Click **Filters** in the header to open the filter panel, and **Close filters** to collapse it. Display bookmarks have Data disabled and target only their intended visuals, so opening or closing the panel preserves selections and metric views.

Dropdown slicers use the supplied dimensions, and equivalent slicers are synchronized across pages. Date bounds are added only where their relationship and scope are suitable: retail revenue/product pages, loan origination dates, and demand historical sales pages. Current-relative date windows are not applied to historical datasets. **Reset filters** clears the page's slicer controls; it does not remove authored metric definitions or permanent analysis filters.

## Hover for context

Custom tooltip pages contain three existing measures and a small trend chart. Hover over a segment, grade, family or city visual that carries the corresponding detail field. Other charts keep their normal contextual tooltips. Demand forecast tooltips are attached to family-level visuals, avoiding an unsupported store-level interpretation of national forecasts.

To configure a tooltip manually: open the hidden Context Tooltip page, choose **Format page > Page information > Tooltip**, then set its canvas type to Tooltip. On a source visual, use **Format visual > General > Tooltips > Type: Report page**, and select Context Tooltip. Keep the category field in the source visual so the hovered filter context flows to the tooltip.

## Drill into details

Select an appropriate data point, then use **Details**, or right-click it and choose **Drill through**. Customer details use Segment, loan details use Grade, forecast details use Product Family, and Zomato details use City. Each detail page includes existing KPI measures, a detail table, and a **Back** action. A drillthrough button is disabled until its required field is available in the selected point.

Available chart drill levels use real source fields: customer Segment to Customer ID; loan Grade to Subgrade; demand State to City to Store; and Zomato City to Restaurant. No category/subcategory or quarter field has been invented.

## Compare metrics and rankings

The overview's metric buttons switch between existing measure views while preserving filter selections. This implementation uses display bookmarks, not new semantic-model field-parameter tables. No existing DAX measure is replaced.

Ranking controls appear on retail Products & Markets, loan Vintage & Exposure, demand Overview, and Zomato Overview. **All**, **Top 5**, **Top 10**, and **Bottom 10** switch visual-level rank views. Rankings use existing raw numerical columns under the selected filter context. The original visual remains available as All; the original Zomato city visual already limits itself to its existing Top 10 measure.

To inspect the implementation in Desktop, open **View > Bookmarks**. Panel and metric bookmarks have Data disabled and Display enabled. New ranking filters are at visual scope; they do not alter SQL, forecast evaluation or the model.

## Formatting settings

Headers use Segoe UI Semibold at 24 pt with zero text-box padding. Chart titles use 13 pt; axes use 10 pt. KPI callouts use 30 pt. Cards have a 14 px corner radius, 10-12 px internal padding, and a subtle shadow at 92% transparency with 7 px blur. Background transparency is 0%. Navigation buttons use 11 pt text and 44-48 px height. The existing chart types and business meanings are retained.

Per-project `visual-audit.json` lists each original data visual by page, identifier and chart type. The source JSON contains its exact formatting, fields and interaction targets.

## Scope and validation

The redesign implements report-page tooltips, drillthrough pages, navigation, display bookmarks, collapsible filters, synchronized dropdowns, applicable date bounds, ranking views, metric views, cross-filtering and light/dark theme files. Model-side field parameters, new risk bands, artificial relative-date defaults, generated narrative claims and ML retraining are not added. Presentation-only context cards count selected categories from existing fields.

Native validation and publication status are recorded separately in DESIGN_STATUS.json and publication receipts. A schema pass alone does not prove that a button or tooltip behaves correctly in Desktop.

Technical references: [Microsoft report-page tooltips](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-tooltips), [Microsoft drillthrough guidance](https://learn.microsoft.com/en-us/power-bi/guidance/report-drillthrough), and [Microsoft report format documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report).
