# Four distinct Power BI layouts

Open a file from `Ready/` with Power BI Desktop. In Desktop edit mode, use Ctrl+click on action buttons.

| Report | Structure | Navigation and lower area |
| --- | --- | --- |
| Customer Analytics | F-shaped reading pattern: KPI band, stacked revenue and returns, tall market comparison | Compact left navigation; metric and ranking controls sit beside their charts |
| Loan Portfolio Analytics | T-shaped review: broad KPI band and central portfolio table with supporting side charts | Horizontal top navigation; comparison controls above the relevant table |
| Retail Demand Forecasting | Split-filter workspace: analysis on the left and a dedicated right filter column | Page navigation at the bottom; ranking and metric controls beside their charts |
| Zomato Restaurant Insights | Hub-and-spoke overview around the service chart, with asymmetric detail canvases | Overview uses central navigation tiles; detail pages use top navigation and vertical KPI stacks |

The existing imported data and DAX measures were retained. The redesign does not refresh data or retrain forecasting models. Power BI Desktop may reserialize the model stream during a native save.

The filter panels, metric views, ranking views, tooltips and drillthrough pages remain available. Demand filters are visible by default in the right column and can be collapsed. On Zomato, the city ranking and metric views are mutually exclusive, preventing stacked alternate charts.

Light and dark theme files are included under each project folder. Header and navigation colors remain fixed for contrast. Previews show the default light theme.
