# Data quality and modeling decisions

The pipeline checks required fields, finite nonnegative sales and promotions, unique IDs and store-family-date keys, unique store keys, known stores and a complete store-family grid on each observed date. Store transaction keys must be unique and nonnegative; missing transaction observations remain missing and are not filled with zero. Raw data is retained unchanged.

Four missing Christmas dates are recorded in data_status.json. The 233-day common complete tail begins 2016-12-26; modeling excludes earlier observations rather than imputing unobserved sales. Descriptive SQL uses the full observed history. Q14 emits NULL where a prior seven-day window would cross a missing day; Q15 joins on an exact calendar-week date.

Promotions are assumed known during the horizon. Holiday exposure unions affected stores, excludes transferred original events and includes effective Transfer events. Two chronological folds select the model, and a third holdout evaluates it. The final model is refitted on the complete modeling window before producing 528 future family-day predictions. Future actuals are unavailable.

Family quantities differ in unit of measure. Reported sales are recorded quantities, not revenue or unconstrained demand. Promotional associations, zero sales and inventory simulations do not establish causal uplift, stockout events or realized savings. See README and DATA_PROVENANCE.json.
