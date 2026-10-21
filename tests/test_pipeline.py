from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
def load(key):
    s=importlib.util.spec_from_file_location(key,BASE/'src/pipeline.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_recursive_forecast_never_uses_future_actuals():
    m=load('demand');days=pd.date_range('2020-01-01',periods=56)
    h=pd.DataFrame({'date':days[:40],'family':'A','sales':np.arange(40)})
    f=pd.DataFrame({'date':days[40:],'family':'A','sales':999999,'promotion_count':0,'holiday_share':0})
    a=m.predict_recursive(h,f,'Seasonal naive');f.sales=-12345;b=m.predict_recursive(h,f,'Seasonal naive')
    pd.testing.assert_frame_equal(a,b)
    assert a.prediction.iloc[7]==a.prediction.iloc[0]


def test_holiday_locale_union_no_double_count():
    m=load('demand');s=pd.DataFrame({'state':['X','Y'],'city':['C','D']})
    h=pd.DataFrame({'date':['2020-01-01']*3,'type':['Holiday']*3,'locale':['Regional','Local','National'],'locale_name':['X','C','All'],'transferred':[False,False,True]})
    assert m.calendar_exposure(h,s).holiday_share.iloc[0]==.5


def test_inventory_stock_conservation_and_nonnegative():
    m=load('demand');r=m.simulate_inventory([20,0,90,30,10,100,0,25,10,5],25,8)
    initial=25*14+1.65*8*np.sqrt(7)
    assert np.isclose(initial+r.arrival_units.sum()-r.fulfilled.sum(),r.ending_stock.iloc[-1])
    assert np.allclose(r.fulfilled+r.lost_sales_units,r.demand)
    assert (r[['ending_stock','order_quantity','lost_sales_units']]>=0).all().all()


def test_no_missing_calendar_days_allowed():
    m=load('demand');d=pd.DataFrame({'date':pd.to_datetime(['2020-01-01','2020-01-03']),'family':'A','sales':1,'promotion_count':0,'holiday_share':0})
    import pytest
    with pytest.raises(ValueError,match='calendar'):m.training_features(d)

def test_four_model_backtest_on_explicit_synthetic_fixture():
    """Exercises fitting and holdout selection; these scores are not real Favorita performance."""
    m=load('demand');days=pd.date_range('2020-01-01',periods=200)
    frames=[]
    for j,family in enumerate(['A','B']):
        frames.append(pd.DataFrame({'date':days,'family':family,'sales':20+j*8+np.sin(np.arange(200)*2*np.pi/7)*4+np.arange(200)*.02,'promotion_count':(np.arange(200)%10==0).astype(int),'holiday_share':0.0}))
    daily=pd.concat(frames,ignore_index=True)
    pred,scores,best,model=m.backtest(daily)
    assert set(scores.method)=={'Seasonal naive','Moving average','Random Forest','XGBoost'}
    assert len(scores)==12 and len(pred)==3*4*16*2
    expected=scores.loc[scores.fold<3].groupby('method').MacroFamilyWAPE.mean().idxmin()
    assert best==expected and (pred.prediction>=0).all()
    assert scores.loc[scores.fold==3,'purpose'].eq('Final holdout').all()

def test_continuous_tail_excludes_gaps_without_imputing_sales():
    m=load('demand');days=pd.date_range('2016-01-01',periods=400)
    d=pd.DataFrame({'date':days,'family':'A','sales':np.arange(400,dtype=float)})
    d=d.loc[d.date.ne(days[100])].copy()
    window,missing=m.continuous_forecast_window(d)
    assert missing.tolist()==[days[100]]
    assert window.date.min()==days[101] and len(window)==299
    assert window.sales.iloc[0]==101
