-- Q01: Daily sales and promotion coverage
SELECT date,SUM(sales) Sales,SUM(onpromotion) PromotionCount,COUNT(*) StoreFamilyRows FROM sales GROUP BY date ORDER BY date;

-- Q02: Monthly trend
WITH m AS (SELECT DATE_FORMAT(date,'%Y-%m') Month,SUM(sales) Sales FROM sales GROUP BY Month) SELECT *,Sales/NULLIF(LAG(Sales) OVER(ORDER BY Month),0)-1 MoMGrowth FROM m;

-- Q03: Store ranking
SELECT store_nbr,SUM(sales) Sales,DENSE_RANK() OVER(ORDER BY SUM(sales) DESC) SalesRank FROM sales GROUP BY store_nbr;

-- Q04: Family mix
SELECT family,SUM(sales) Sales,SUM(sales)/NULLIF(SUM(SUM(sales)) OVER(),0) SalesShare FROM sales GROUP BY family;

-- Q05: City and state contribution
SELECT d.state,d.city,SUM(s.sales) Sales FROM sales s JOIN stores d USING(store_nbr) GROUP BY d.state,d.city;

-- Q06: Store type performance
SELECT d.type,COUNT(DISTINCT d.store_nbr) Stores,SUM(s.sales) Sales FROM sales s JOIN stores d USING(store_nbr) GROUP BY d.type;

-- Q07: Weekday seasonality
SELECT WEEKDAY(date) Weekday,SUM(sales) Sales,COUNT(DISTINCT date) Days,SUM(sales)/COUNT(DISTINCT date) SalesPerObservedDay FROM sales GROUP BY Weekday;

-- Q08: Monthly family seasonality
SELECT family,MONTH(date) MonthOfYear,SUM(sales) Sales,COUNT(DISTINCT date) Days FROM sales GROUP BY family,MonthOfYear;

-- Q09: Promotion association, not causal uplift
SELECT CASE WHEN onpromotion>0 THEN 'Promoted' ELSE 'Not promoted' END PromotionGroup,COUNT(*) RowsObserved,AVG(sales) MeanSales FROM sales GROUP BY PromotionGroup;

-- Q10: Promotion coverage by family
SELECT family,SUM(onpromotion>0)/COUNT(*) PromotedRowShare,SUM(onpromotion) PromotionCount FROM sales GROUP BY family;

-- Q11: Zero recorded sales
SELECT family,SUM(sales=0) ZeroRows,COUNT(*) RowsObserved,SUM(sales=0)/COUNT(*) ZeroShare FROM sales GROUP BY family;

-- Q12: Store transactions
SELECT store_nbr,SUM(transactions) Transactions,COUNT(DISTINCT date) ObservedDays FROM transactions GROUP BY store_nbr;

-- Q13: Sales units per store transaction
WITH s AS (SELECT date,store_nbr,SUM(sales) Sales FROM sales GROUP BY date,store_nbr) SELECT s.store_nbr,SUM(s.Sales)/NULLIF(SUM(t.transactions),0) UnitsPerTransaction FROM s JOIN transactions t USING(date,store_nbr) GROUP BY s.store_nbr;

-- Q14: Prior seven calendar days; return NULL whenever the seven-day history crosses a missing day
SELECT family,date,Sales,CASE WHEN DATEDIFF(date,LAG(date,7) OVER(PARTITION BY family ORDER BY date))=7 THEN AVG(Sales) OVER(PARTITION BY family ORDER BY date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) END Prior7Mean FROM (SELECT family,date,SUM(sales) Sales FROM sales GROUP BY family,date) x;

-- Q15: Calendar-week lag on exact date
WITH d AS (SELECT family,date,SUM(sales) Sales FROM sales GROUP BY family,date) SELECT a.family,a.date,a.Sales,b.Sales PriorWeekSales FROM d a LEFT JOIN d b ON a.family=b.family AND b.date=DATE_SUB(a.date,INTERVAL 7 DAY);

-- Q16: Within-store largest family
WITH d AS (SELECT store_nbr,family,SUM(sales) Sales FROM sales GROUP BY store_nbr,family),r AS (SELECT *,ROW_NUMBER() OVER(PARTITION BY store_nbr ORDER BY Sales DESC,family) rn FROM d) SELECT * FROM r WHERE rn=1;

-- Q17: Missing store transaction matches
SELECT COUNT(*) MissingStoreDays FROM (SELECT DISTINCT date,store_nbr FROM sales) s LEFT JOIN transactions t USING(date,store_nbr) WHERE t.store_nbr IS NULL;

-- Q18: Effective holiday store exposure without duplicate sales
SELECT s.date,d.store_nbr,MAX(CASE WHEN h.event_id IS NOT NULL THEN 1 ELSE 0 END) EffectiveHoliday FROM (SELECT DISTINCT date FROM sales) s CROSS JOIN stores d LEFT JOIN holidays h ON h.date=s.date AND LOWER(h.transferred)='false' AND h.type IN ('Holiday','Additional','Bridge','Transfer') AND (h.locale='National' OR h.locale='Regional' AND h.locale_name=d.state OR h.locale='Local' AND h.locale_name=d.city) GROUP BY s.date,d.store_nbr;

-- Q19: Extreme observations for manual review
SELECT id,date,store_nbr,family,sales,onpromotion FROM sales ORDER BY sales DESC LIMIT 30;

-- Q20: Family variability, not a calibrated forecast
WITH d AS (SELECT family,date,SUM(sales) Sales FROM sales GROUP BY family,date) SELECT family,AVG(Sales) MeanDailySales,STDDEV_SAMP(Sales) DailyStd,STDDEV_SAMP(Sales)/NULLIF(AVG(Sales),0) CoefficientVariation FROM d GROUP BY family;
