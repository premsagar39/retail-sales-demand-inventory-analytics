# Quality status

| Check | Status | Evidence |
|---|---|---|
| Source provenance | Pass | DATA_PROVENANCE.json; archive hashes; supplied holiday file matched exactly |
| Real-data Python pipeline | Pass | 3,000,888 sales rows; data_status.json |
| MySQL analyses | Pass | 21 real-data queries; sql_execution.json |
| Python and MySQL controls | Pass | mysql_validation.json; row count, dates and sales totals reconcile |
| Behavioral tests | Pass | 6 tests; synthetic fixtures label behavior only |
| Results recomputation | Pass | 6,336 backtest rows; all 12 score rows; 99 inventory paths; 528 future predictions |
| Power BI report definition | Pass | 54 files validate against Microsoft public JSON schemas |
| Native Power BI refresh | Pass | 5 pages inspected; 26 measures in model; cached PBIX saved natively |
| DAX independent API execution | Not performed | Native forecast cards match Python; no claim every expression was tested independently |
| Holdout protection | Pass | Two selection folds; separate final holdout; no future target in recursive lags |
| Forecast results | Pass | Random Forest pooled WAPE 9.58%; macro-family WAPE 22.12% |
| Inventory interpretation | Pass | Short, labeled scenario; no real savings or deployment claim |
| Public GitHub publication | Published | https://github.com/premsagar39/retail-sales-demand-inventory-analytics; original data and cached PBIX excluded |
| LinkedIn publication | Published | [Project post](https://www.linkedin.com/feed/update/urn:li:activity:7518476333258182656/); included in LinkedIn Featured |

Comparison extension: SQL Q21 reconciles with Python. Two new DAX measures and the comparison page were inspected in Power BI Desktop; the updated PBIX was saved natively. See comparison_native_validation.json.
