# Measure definitions

Forecast cards always use fold 3 and the model selected on folds 1–2. Macro WAPE averages nonblank family WAPE; pooled WAPE weights by recorded quantities. Scores model chart is a fixed full-portfolio comparison and does not respond to the family slicer. Future has its own date column to preserve dates beyond the observed sales dimension. Inventory measures default to z=1.65 when multiple z values are in context; row comparisons evaluate each z separately. Transaction counts are store-day counts and do not filter by family.

## Recorded Sales

```dax
SUM(Sales[sales])
```

## Sales Rows

```dax
COUNTROWS(Sales)
```

## Stores Observed

```dax
DISTINCTCOUNT(Sales[store_nbr])
```

## Families Observed

```dax
DISTINCTCOUNT(Sales[family])
```

## Observed Sales Days

```dax
DISTINCTCOUNT(Sales[date])
```

## Sales per Observed Day

```dax
DIVIDE([Recorded Sales],[Observed Sales Days])
```

## Promotion Items

```dax
SUM(Sales[onpromotion])
```

## Promoted Row Share

```dax
DIVIDE(CALCULATE([Sales Rows],Sales[onpromotion]>0),[Sales Rows])
```

## Zero Recorded Sales Share

```dax
DIVIDE(CALCULATE([Sales Rows],Sales[sales]=0),[Sales Rows])
```

## Store Transactions

```dax
SUM(Transactions[transactions])
```

## Selected Forecast Model

```dax
MAX(Selection[SelectedModel])
```

## Holdout Actual

```dax
VAR M=[Selected Forecast Model] RETURN CALCULATE(SUM(Forecasts[sales]),Forecasts[fold]=3,Forecasts[method]=M)
```

## Holdout Forecast

```dax
VAR M=[Selected Forecast Model] RETURN CALCULATE(SUM(Forecasts[prediction]),Forecasts[fold]=3,Forecasts[method]=M)
```

## Holdout Absolute Error

```dax
VAR M=[Selected Forecast Model] RETURN CALCULATE(SUMX(Forecasts,ABS(Forecasts[sales]-Forecasts[prediction])),Forecasts[fold]=3,Forecasts[method]=M)
```

## Holdout WAPE

```dax
DIVIDE([Holdout Absolute Error],[Holdout Actual])
```

## Holdout Macro Family WAPE

```dax
AVERAGEX(VALUES(Families[family]),[Holdout WAPE])
```

## Holdout MAE

```dax
VAR M=[Selected Forecast Model] RETURN DIVIDE([Holdout Absolute Error],CALCULATE(COUNTROWS(Forecasts),Forecasts[fold]=3,Forecasts[method]=M))
```

## Model WAPE Full Portfolio

```dax
CALCULATE(MAX(Scores[WAPE]),Scores[fold]=3)
```

## Future Forecast

```dax
SUM(Future[prediction])
```

## Scenario Z

```dax
SELECTEDVALUE(Inventory[service_z],1.65)
```

## Scenario Fill Rate

```dax
VAR Z=[Scenario Z] RETURN DIVIDE(CALCULATE(SUM(Inventory[fulfilled]),Inventory[service_z]=Z),CALCULATE(SUM(Inventory[demand]),Inventory[service_z]=Z))
```

## Scenario Lost Sales

```dax
VAR Z=[Scenario Z] RETURN CALCULATE(SUM(Inventory[lost_sales_units]),Inventory[service_z]=Z)
```

## Scenario Mean Stock

```dax
VAR Z=[Scenario Z] RETURN CALCULATE(AVERAGE(Inventory[ending_stock]),Inventory[service_z]=Z)
```

## Assumed Holding Cost

```dax
VAR Z=[Scenario Z] RETURN CALCULATE(SUM(Inventory[holding_cost_assumed]),Inventory[service_z]=Z)
```

## Holdout Signed Error

Selected-model fold-3 forecast minus actual, respecting date and family filters.

```dax
[Holdout Forecast]-[Holdout Actual]
```

## Holdout Bias

Signed error / actual. Positive means overforecasting; zero actual gives blank. Different from WAPE.

```dax
DIVIDE([Holdout Signed Error],[Holdout Actual])
```
