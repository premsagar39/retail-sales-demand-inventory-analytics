"""Rebuild the comparison export, chart and offline dashboard from project results."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
root=Path(__file__).resolve().parents[1]
key='demand'
title='Forecast bias and absolute error'
accent='#216EAF'

if key=='retail':
 source=pd.read_csv(root/'data/processed/customer_rfm.csv')
 summary=source.groupby('Segment').agg(Customers=('CustomerID','count'),GrossSpend=('Monetary','sum'),SpendPerCustomer=('Monetary','mean')).reset_index()
 summary['SpendIndex']=summary.SpendPerCustomer/(summary.GrossSpend.sum()/summary.Customers.sum())
 summary['SpendRank']=summary.SpendPerCustomer.rank(method='dense',ascending=False).astype(int)
elif key=='loans':
 summary=pd.read_csv(root/'data/exports/vintage_portfolio.csv')
else:
 status=json.loads((root/'reports/data_status.json').read_text(encoding='utf-8'))
 source=pd.read_csv(root/'data/exports/backtest_predictions.csv');source=source[source.fold.eq(3)&source.method.eq(status['best_model_selected_on_folds_1_2'])]
 summary=source.groupby('family').agg(Actual=('sales','sum'),Forecast=('prediction','sum')).reset_index()
 summary['SignedError']=summary.Forecast-summary.Actual
 summary['Bias']=summary.SignedError/summary.Actual.replace(0,float('nan'))
summary.to_csv(root/'data/exports/comparison_review.csv',index=False)

df=pd.read_csv(root/'data/exports/comparison_review.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','figure.facecolor':'#F3F6FA','axes.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'text.color':'#17324D','axes.labelcolor':'#17324D'})
fig,ax=plt.subplots(1,2,figsize=(14,6),layout='constrained');web=make_subplots(rows=1,cols=2)
if key=='retail':
 df=df.sort_values('SpendPerCustomer');ax[0].barh(df.Segment,df.SpendPerCustomer,color=accent);ax[0].set_title('Gross purchase spend per customer (GBP)');ax[1].barh(df.Segment,df.SpendIndex,color='#D8A840');ax[1].axvline(1,color='#17324D',ls='--');ax[1].set_title('Index: selected full-period customer benchmark = 1')
 web.add_trace(go.Bar(y=df.Segment,x=df.SpendPerCustomer,orientation='h',name='GBP per customer',marker_color=accent),row=1,col=1);web.add_trace(go.Bar(y=df.Segment,x=df.SpendIndex,orientation='h',name='Spend index',marker_color='#D8A840'),row=1,col=2)
 note='Full-period RFM snapshot: 10 Dec 2011. Historical spend; no campaign uplift or recoverable-revenue claim.'
elif key=='loans':
 ax[0].plot(df.VintageYear,df.BadResolvedShare*100,'o-',color=accent,label='Charged off / resolved');ax[0].plot(df.VintageYear,df.ResolvedShare*100,'o-',color='#D8A840',label='Resolved / all');ax[0].legend();ax[0].set_ylabel('Percent');ax[0].set_title('Read the outcome rate alongside resolved coverage')
 gap=100*(df.BadResolvedShare-df.BadResolvedLoans.sum()/df.ResolvedLoans.sum());ax[1].bar(df.VintageYear,gap,color=accent);ax[1].axhline(0,color='#17324D');ax[1].set_ylabel('Percentage points');ax[1].set_title('Outcome gap vs weighted portfolio benchmark')
 for c,n,col in [('BadResolvedShare','Charged off / resolved',accent),('ResolvedShare','Resolved / all','#D8A840')]:web.add_trace(go.Scatter(x=df.VintageYear,y=df[c]*100,name=n,line_color=col),row=1,col=1)
 web.add_trace(go.Bar(x=df.VintageYear,y=gap,name='Outcome gap (pp)',marker_color=accent),row=1,col=2)
 note='Accepted loans only; historical status snapshot. Vintage gaps are descriptive and are not adjusted for maturity.'
else:
 pred=pd.read_csv(root/'data/exports/backtest_predictions.csv');s=json.loads((root/'reports/data_status.json').read_text(encoding='utf-8'));p=pred[pred.fold.eq(3)&pred.method.eq(s['best_model_selected_on_folds_1_2'])]
 w=p.assign(AE=(p.sales-p.prediction).abs()).groupby('family').agg(AE=('AE','sum'),Actual=('sales','sum'));w['WAPE']=w.AE/w.Actual
 df=df.merge(w.WAPE,left_on='family',right_index=True);view=df.assign(AbsBias=df.Bias.abs()).nlargest(10,'AbsBias').sort_values('Bias')
 ax[0].barh(view.family,view.Bias*100,color=[accent if x>=0 else '#BC5B55' for x in view.Bias]);ax[0].axvline(0,color='#17324D');ax[0].set_title('Largest absolute family bias (%)');ax[1].scatter(df.Bias*100,df.WAPE*100,c=accent);ax[1].set_xlabel('Signed bias (%)');ax[1].set_ylabel('WAPE (%)');ax[1].set_title('Bias can cancel; absolute error remains visible')
 web.add_trace(go.Bar(y=df.family,x=df.Bias*100,orientation='h',name='Bias (%)',marker_color=accent),row=1,col=1);web.add_trace(go.Scatter(x=df.Bias*100,y=df.WAPE*100,text=df.family,mode='markers',name='Family errors',marker_color=accent),row=1,col=2)
 note='Selected Random Forest, final 16-day holdout only. Positive bias = overforecast. Small-family percentages can be large.'
fig.suptitle(title,fontsize=20,fontweight='bold');fig.supxlabel(note,fontsize=10)
fig.savefig(root/'reports/figures/comparison_review.png',dpi=150);plt.close(fig)
web.update_layout(title=title,height=720,paper_bgcolor='#F3F6FA',plot_bgcolor='white',font={'family':'Arial','color':'#17324D'},margin={'b':110},annotations=list(web.layout.annotations)+[dict(text=note,x=0,y=-.16,xref='paper',yref='paper',showarrow=False,xanchor='left')])
web.write_html(root/'reports/Comparison_Dashboard.html',include_plotlyjs="cdn",full_html=True)

print(key,'comparison preview and offline dashboard saved')
