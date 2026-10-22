# Retail Demand Forecasting

Sales analysis and short-term forecasting using 3,000,888 Favorita records across 54 stores and 33 product families. Forecasts are evaluated on future time blocks before being used in illustrative inventory scenarios.

![Retail Demand Forecasting dashboard](reports/figures/project_overview.png)

**Python · pandas · scikit-learn · XGBoost · MySQL · Power BI · DAX**

## Forecast results

| Final holdout: 31 July–15 August 2017 | Result |
| --- | ---: |
| Selected model | Random Forest |
| Pooled WAPE | 9.58% |
| Macro-family WAPE | 22.12% |
| Seasonal-naive pooled WAPE | 12.82% |
| MAE per national family-day | 2,415.82 |

The model was selected on two earlier 16-day folds using mean macro-family WAPE. The final holdout was kept separate from model selection. Moving Average, Seasonal Naive, Random Forest and XGBoost were compared.

## Analysis

The project covers sales patterns, promotions, seasonality, forecast errors and assumed service–stock trade-offs. Family-level bias and WAPE show where an overall sales-weighted score hides poor performance. Small categories remain difficult: BOOKS has 242.73% holdout WAPE.

The five-page Power BI report has 26 DAX measures, a dedicated right filter column and bottom navigation. Inventory scenarios use stated lead-time, service-factor and holding-cost assumptions.

## Explore

- [21 SQL analyses](sql/analysis_queries.sql) and [schema](sql/schema.sql)
- [Executed notebook](notebooks/01_analysis.ipynb) and [forecasting pipeline](src/pipeline.py)
- [Power BI project](powerbi/Retail_Demand_Inventory.pbip) and [DAX measures](powerbi/measures.dax)
- [Forecast error review](reports/figures/comparison_review.png)
- [Model results](data/exports/forecast_metrics.csv), [family errors](data/exports/family_forecast_metrics.csv) and [fold dates](data/exports/fold_dates.csv)
- [Data dictionary](reports/DATA_DICTIONARY.md), [methodology](reports/DATA_QUALITY.md) and [measure definitions](powerbi/MEASURE_DEFINITIONS.md)

## Run locally

Use Python 3.12. Download `train.csv`, `stores.csv`, `transactions.csv` and `holidays_events.csv` from the [Favorita competition](https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data). Include `test.csv` for the 528 forward forecasts.

```bash
pip install -r requirements.txt
python src/pipeline.py --source-dir "path/to/favorita-files"
python src/reporting.py
python src/comparison_analysis.py
python -m pytest tests -q
```

For MySQL 8, create an empty local database, set `DATABASE_URL` in the environment using `.env.example`, enable LOCAL INFILE and run `python src/database.py`. In Power BI Desktop, open the PBIP, set `DataRoot` to the generated `data/` folder with a trailing slash and refresh. Themes are in `powerbi/themes/`.

## Data notes

Forecasts target national daily sales by family, using a complete 233-day window to avoid calendar gaps in lag features. Predictions use recursive history; future actual sales do not enter training. Promotion counts are assumed known. Combined sales are recorded quantities, not revenue. Inventory outputs are scenarios, not measured operational savings. See [data provenance](reports/DATA_PROVENANCE.json) for source hashes. Code is covered by [MIT](LICENSE).
