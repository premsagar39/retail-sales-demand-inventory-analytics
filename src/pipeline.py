"""Favorita analytics with recursive, chronological forecasts and labeled inventory scenarios."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
ROOT=Path(__file__).resolve().parents[1]
FEATURES=['family_code','weekday','month','day','promotion_count','holiday_share','lag1','lag7','lag14','lag28','mean7','mean28']

def calendar_exposure(holidays,stores):
    """Count affected stores once per date; transferred holidays are not effective holidays."""
    h=holidays.copy();h['date']=pd.to_datetime(h.date)
    h=h.loc[~h.transferred.astype(str).str.lower().eq('true') & h.type.isin(['Holiday','Additional','Bridge','Transfer'])]
    rows=[]
    for day,group in h.groupby('date'):
        affected=pd.Series(False,index=stores.index)
        for row in group.itertuples():
            if row.locale=='National':affected|=True
            elif row.locale=='Regional':affected|=stores.state.eq(row.locale_name)
            elif row.locale=='Local':affected|=stores.city.eq(row.locale_name)
        rows.append((day,float(affected.mean())))
    return pd.DataFrame(rows,columns=['date','holiday_share'])

def feature_row(history,family,day,promo,holiday,code):
    """All demand predictors end strictly before the predicted day."""
    values=np.asarray(history[family],dtype=float)
    if len(values)<28:raise ValueError('Each series needs at least 28 earlier daily observations')
    return [code,day.weekday(),day.month,day.day,promo,holiday,values[-1],values[-7],values[-14],values[-28],values[-7:].mean(),values[-28:].mean()]

def training_features(daily):
    d=daily.sort_values(['family','date']).copy()
    validate_daily_calendar(d)
    codes={f:i for i,f in enumerate(sorted(d.family.unique()))}
    d['family_code']=d.family.map(codes);d['weekday']=d.date.dt.weekday;d['month']=d.date.dt.month;d['day']=d.date.dt.day
    for n in [1,7,14,28]:d[f'lag{n}']=d.groupby('family').sales.shift(n)
    for n in [7,28]:d[f'mean{n}']=d.groupby('family').sales.transform(lambda s:s.shift(1).rolling(n).mean())
    return d.dropna(subset=FEATURES),codes

def predict_recursive(history,future,method,model=None,codes=None):
    hist={f:list(g.sort_values('date').sales) for f,g in history.groupby('family')};rows=[]
    for day,group in future.sort_values(['date','family']).groupby('date'):
        batch=None
        if method not in ['Seasonal naive','Moving average']:
            features=[feature_row(hist,r.family,day,r.promotion_count,r.holiday_share,codes[r.family]) for r in group.itertuples()]
            batch=model.predict(pd.DataFrame(features,columns=FEATURES))
        for j,r in enumerate(group.itertuples()):
            if method=='Seasonal naive':pred=hist[r.family][-7]
            elif method=='Moving average':pred=float(np.mean(hist[r.family][-28:]))
            else:
                pred=float(batch[j])
            pred=max(0,pred);hist[r.family].append(pred);rows.append((day,r.family,pred))
    return pd.DataFrame(rows,columns=['date','family','prediction'])

def evaluate(actual,predicted):
    error=np.asarray(predicted)-np.asarray(actual)
    denom=np.abs(actual).sum()
    return {'MAE':float(np.mean(np.abs(error))),'RMSE':float(np.sqrt(np.mean(error**2))),'WAPE':float(np.abs(error).sum()/denom) if denom else None}

def backtest(daily,horizon=16):
    """Two model-selection folds followed by a separate untouched final holdout."""
    validate_daily_calendar(daily)
    days=sorted(daily.date.unique())
    if len(days)<180:raise ValueError('At least 180 observed days are required')
    all_predictions=[];metrics=[];trained={}
    methods=['Seasonal naive','Moving average','Random Forest','XGBoost']
    for fold,cut in enumerate([len(days)-3*horizon,len(days)-2*horizon,len(days)-horizon],1):
        train=daily.loc[daily.date<days[cut]];future=daily.loc[(daily.date>=days[cut])&(daily.date<=days[cut+horizon-1])]
        features,codes=training_features(train)
        for method in methods:
            model=None
            if method=='Random Forest':model=RandomForestRegressor(n_estimators=120,min_samples_leaf=4,max_depth=16,random_state=42,n_jobs=2)
            if method=='XGBoost':model=XGBRegressor(n_estimators=200,max_depth=5,learning_rate=.06,subsample=.9,colsample_bytree=.9,objective='reg:squarederror',random_state=42,n_jobs=2)
            if model is not None:model.fit(features[FEATURES],features.sales)
            prediction=predict_recursive(train,future,method,model,codes).merge(future[['date','family','sales']],on=['date','family'])
            prediction['method']=method;prediction['fold']=fold;all_predictions.append(prediction)
            family_metrics=[evaluate(g.sales,g.prediction)['WAPE'] for _,g in prediction.groupby('family')]
            metrics.append({'fold':fold,'purpose':'Final holdout' if fold==3 else 'Model selection','method':method,'MacroFamilyWAPE':float(np.mean([x for x in family_metrics if x is not None])),**evaluate(prediction.sales,prediction.prediction)})
            trained[(fold,method)]=(model,codes)
    scores=pd.DataFrame(metrics)
    best=scores.loc[scores.fold.lt(3)].groupby('method').MacroFamilyWAPE.mean().idxmin()
    return pd.concat(all_predictions,ignore_index=True),scores,best,trained[(3,best)]

def simulate_inventory(actual,mean_demand,std_demand,lead_days=7,review_days=7,z=1.65,holding_cost=.01):
    """Lost-sales daily simulation; costs and lead times are assumptions, not source observations."""
    if lead_days<1 or review_days<1 or mean_demand<0 or std_demand<0 or z<0 or holding_cost<0 or np.any(np.asarray(actual)<0):raise ValueError('Invalid inventory assumption')
    safety=z*std_demand*np.sqrt(lead_days);rop=mean_demand*lead_days+safety;target=mean_demand*(lead_days+review_days)+safety
    stock=target;orders=[];rows=[]
    for t,demand in enumerate(actual):
        arrived=sum(q for due,q in orders if due==t);orders=[(due,q) for due,q in orders if due>t];stock+=arrived
        fulfilled=min(stock,max(0,demand));lost=max(0,demand-fulfilled);stock-=fulfilled
        position=stock+sum(q for _,q in orders);quantity=max(0,target-position) if t%review_days==0 else 0
        if quantity:orders.append((t+lead_days,quantity))
        rows.append({'day':t,'demand':demand,'fulfilled':fulfilled,'lost_sales_units':lost,'ending_stock':stock,'order_quantity':quantity,'arrival_units':arrived,'holding_cost_assumed':stock*holding_cost,'safety_stock':safety,'reorder_point':rop})
    return pd.DataFrame(rows)

def validate_daily_calendar(daily):
    """Fail rather than silently treating missing dates as zero demand or shifting calendar lags."""
    expected=pd.date_range(daily.date.min(),daily.date.max())
    for family,g in daily.groupby('family'):
        if g.date.duplicated().any() or len(g)!=len(expected) or not pd.DatetimeIndex(g.date.sort_values()).equals(expected):
            raise ValueError(f'Incomplete daily calendar for {family}; resolve missing dates explicitly before forecasting')

def continuous_forecast_window(daily):
    """Use the complete common daily tail; never impute unobserved demand."""
    dates=pd.DatetimeIndex(sorted(daily.date.unique()))
    missing=pd.date_range(dates.min(),dates.max()).difference(dates)
    start=missing.max()+pd.Timedelta(days=1) if len(missing) else dates.min()
    window=daily.loc[daily.date.ge(start)].copy()
    validate_daily_calendar(window)
    if window.date.nunique()<180:raise ValueError('Fewer than 180 complete daily observations after the last gap')
    return window,missing

def run(source_dir,root=ROOT):
    root=Path(root);source_dir=Path(source_dir);processed=root/'data/processed';exports=root/'data/exports';reports=root/'reports'
    for p in [processed,exports,reports]:p.mkdir(parents=True,exist_ok=True)
    holiday_path=source_dir/'holidays_events.csv'
    if not holiday_path.is_file():raise FileNotFoundError(holiday_path)
    holidays=pd.read_csv(holiday_path);holidays['event_id']=range(1,len(holidays)+1)
    holidays[['event_id','date','type','locale','locale_name','description','transferred']].to_csv(processed/'holidays.csv',index=False)
    holidays.groupby(['type','locale']).size().rename('Events').reset_index().to_csv(exports/'holiday_calendar_summary.csv',index=False)
    missing=[name for name in ['train.csv','stores.csv','transactions.csv'] if not (source_dir/name).is_file()]
    status={'source':'Favorita Store Sales competition','holiday_records':len(holidays),'missing_files':missing,'status':'Awaiting sales data' if missing else 'Processing','forecast_results_available':False}
    (reports/'data_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    if missing:print(json.dumps(status,indent=2),flush=True);return status
    sales=pd.read_csv(source_dir/'train.csv',parse_dates=['date']);stores=pd.read_csv(source_dir/'stores.csv');transactions=pd.read_csv(source_dir/'transactions.csv',parse_dates=['date'])
    if stores.store_nbr.isna().any() or stores.store_nbr.duplicated().any():raise ValueError('Invalid store dimension')
    required=['id','date','store_nbr','family','sales','onpromotion']
    if sales[required].isna().any().any() or sales.date.isna().any():raise ValueError('Null required sales field')
    if not np.isfinite(sales[['sales','onpromotion']].to_numpy()).all() or sales.onpromotion.lt(0).any():raise ValueError('Invalid numeric sales field')
    if sales.duplicated(['date','store_nbr','family']).any() or sales.id.duplicated().any():raise ValueError('Duplicate sales keys')
    if not sales.store_nbr.isin(stores.store_nbr).all():raise ValueError('Unknown store keys')
    if sales.sales.isna().any() or sales.sales.lt(0).any():raise ValueError('Missing or negative sales')
    if transactions.duplicated(['date','store_nbr']).any():raise ValueError('Duplicate store transaction keys')
    if not transactions.store_nbr.isin(stores.store_nbr).all() or transactions.transactions.isna().any() or transactions.transactions.lt(0).any():raise ValueError('Invalid transaction data')
    expected=stores.store_nbr.nunique()*sales.family.nunique()
    if not sales.groupby('date').size().eq(expected).all():raise ValueError('Incomplete store-family grid on observed dates')
    calendar=calendar_exposure(holidays,stores)
    daily=sales.groupby(['date','family']).agg(sales=('sales','sum'),promotion_count=('onpromotion','sum')).reset_index().merge(calendar,on='date',how='left').fillna({'holiday_share':0})
    window,missing_days=continuous_forecast_window(daily)
    daily.to_csv(exports/'daily_family_sales.csv',index=False,date_format='%Y-%m-%d')
    print('Training four models on complete daily tail: '+str(window.date.min().date())+' to '+str(window.date.max().date()),flush=True)
    predictions,metrics,best,_=backtest(window)
    dates_sorted=sorted(window.date.unique());folds=[]
    for fold,cut in enumerate([len(dates_sorted)-48,len(dates_sorted)-32,len(dates_sorted)-16],1):
        folds.append({'fold':fold,'train_start':str(pd.Timestamp(dates_sorted[0]).date()),'train_end':str(pd.Timestamp(dates_sorted[cut-1]).date()),'evaluation_start':str(pd.Timestamp(dates_sorted[cut]).date()),'evaluation_end':str(pd.Timestamp(dates_sorted[cut+15]).date()),'purpose':'Final holdout' if fold==3 else 'Model selection'})
    pd.DataFrame(folds).to_csv(exports/'fold_dates.csv',index=False)
    predictions.to_csv(exports/'backtest_predictions.csv',index=False);metrics.to_csv(exports/'forecast_metrics.csv',index=False)
    final_metrics=metrics.loc[metrics.fold.eq(3)&metrics.method.eq(best)].iloc[0].to_dict()
    family_scores=[]
    for (fold,method,family),g in predictions.groupby(['fold','method','family']):
        family_scores.append({'fold':fold,'method':method,'family':family,**evaluate(g.sales,g.prediction)})
    pd.DataFrame(family_scores).to_csv(exports/'family_forecast_metrics.csv',index=False)
    final=predictions.loc[predictions.fold.eq(3)&predictions.method.eq(best)]
    inventory=[]
    for family,g in final.groupby('family'):
        start=g.date.min();history=window.loc[window.family.eq(family)&window.date.lt(start)].sort_values('date').tail(28)
        for z in [0,1.28,1.65]:
            sim=simulate_inventory(g.sort_values('date').sales.to_numpy(),float(g.prediction.mean()),float(history.sales.std()),z=z)
            sim['family']=family;sim['service_z']=z;inventory.append(sim)
    inv=pd.concat(inventory,ignore_index=True)
    inv['date']=pd.to_datetime(final.date.min())+pd.to_timedelta(inv.day,unit='D')
    inv.to_csv(exports/'inventory_simulation.csv',index=False,date_format='%Y-%m-%d')
    summary=inv.groupby('service_z').agg(demand=('demand','sum'),fulfilled=('fulfilled','sum'),lost_sales_units=('lost_sales_units','sum'),mean_ending_stock=('ending_stock','mean'),holding_cost_assumed=('holding_cost_assumed','sum')).reset_index()
    summary['fill_rate']=summary.fulfilled/summary.demand
    summary.to_csv(exports/'inventory_scenarios.csv',index=False)
    # Refit the frozen method on all modeling history for a genuine future horizon.
    if (source_dir/'test.csv').is_file():
        future_raw=pd.read_csv(source_dir/'test.csv',parse_dates=['date'])
        if future_raw.duplicated(['date','store_nbr','family']).any():raise ValueError('Duplicate future sales keys')
        if future_raw.date.min()!=window.date.max()+pd.Timedelta(days=1):raise ValueError('Future forecast must start on the next day')
        future=future_raw.groupby(['date','family']).agg(promotion_count=('onpromotion','sum')).reset_index().merge(calendar,on='date',how='left').fillna({'holiday_share':0})
        if set(future.family)!=set(window.family) or not future.groupby('date').size().eq(window.family.nunique()).all():raise ValueError('Incomplete future family grid')
        features,codes=training_features(window);model=None
        if best=='Random Forest':model=RandomForestRegressor(n_estimators=120,min_samples_leaf=4,max_depth=16,random_state=42,n_jobs=2)
        if best=='XGBoost':model=XGBRegressor(n_estimators=200,max_depth=5,learning_rate=.06,subsample=.9,colsample_bytree=.9,objective='reg:squarederror',random_state=42,n_jobs=2)
        if model is not None:model.fit(features[FEATURES],features.sales)
        forecast=predict_recursive(window,future,best,model,codes);forecast['method']=best
        forecast.to_csv(exports/'future_forecast.csv',index=False,date_format='%Y-%m-%d')
        status['future_forecast_rows']=len(forecast)
    for col,file in [('store_nbr','store_performance'),('family','family_performance')]:sales.groupby(col).agg(Sales=('sales','sum'),PromotionCount=('onpromotion','sum')).reset_index().to_csv(exports/(file+'.csv'),index=False)
    sales.groupby(pd.Grouper(key='date',freq='MS')).agg(Sales=('sales','sum'),PromotionCount=('onpromotion','sum')).reset_index().to_csv(exports/'monthly_sales.csv',index=False)
    enriched=sales.merge(stores,on='store_nbr',validate='many_to_one')
    sales['Promoted']=sales.onpromotion.gt(0).astype(int)
    sales.groupby('Promoted').agg(Rows=('id','size'),Sales=('sales','sum'),MeanSales=('sales','mean')).reset_index().to_csv(exports/'promotion_summary.csv',index=False)
    enriched.groupby('state').agg(Sales=('sales','sum'),StoreCount=('store_nbr','nunique')).reset_index().to_csv(exports/'state_sales.csv',index=False)
    dates=pd.DataFrame({'date':pd.date_range(sales.date.min(),sales.date.max())});dates['year']=dates.date.dt.year;dates['month']=dates.date.dt.strftime('%Y-%m');dates['weekday']=dates.date.dt.weekday
    for name,frame in [('sales',sales[['id','date','store_nbr','family','sales','onpromotion']]),('stores',stores),('families',sales[['family']].drop_duplicates()),('dates',dates),('transactions',transactions)]:frame.to_csv(processed/(name+'.csv'),index=False,date_format='%Y-%m-%d')
    status.update(status='Analysis executed',forecast_results_available=True,sales_rows=len(sales),sales_total=float(sales.sales.sum()),stores=len(stores),families=int(sales.family.nunique()),observed_days=int(sales.date.nunique()),date_min=str(sales.date.min().date()),date_max=str(sales.date.max().date()),missing_calendar_dates=[str(x.date()) for x in missing_days],model_window_start=str(window.date.min().date()),model_window_days=int(window.date.nunique()),best_model_selected_on_folds_1_2=best,final_holdout=final_metrics,holdout_days=16,inventory_assumptions={'lead_days':7,'review_days':7,'z_values':[0,1.28,1.65],'assumed_cost_per_unit_day':.01,'cost_currency':'scenario units, not observed money','stockout_policy':'lost sales'},forecast_grain='National daily sales per family; store comparisons remain descriptive')
    (reports/'data_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8');return status

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-dir',required=True,type=Path);a=p.parse_args();run(a.source_dir)
