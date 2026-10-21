"""Rebuild visual evidence from the pipeline's real aggregate exports."""
from pathlib import Path
import json,html
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import nbformat

ROOT=Path(__file__).resolve().parents[1]

def run(root=ROOT):
    root=Path(root);ex=root/'data/exports';reports=root/'reports';figures=reports/'figures';figures.mkdir(exist_ok=True)
    status=json.loads((reports/'data_status.json').read_text());winner=status['best_model_selected_on_folds_1_2']
    scores=pd.read_csv(ex/'forecast_metrics.csv');pred=pd.read_csv(ex/'backtest_predictions.csv',parse_dates=['date'])
    holdout=pred.loc[pred.fold.eq(3)&pred.method.eq(winner)].copy()
    totals=holdout.groupby('date')[['sales','prediction']].sum()
    inventory=pd.read_csv(ex/'inventory_scenarios.csv');future=pd.read_csv(ex/'future_forecast.csv',parse_dates=['date']).groupby('date').prediction.sum()
    monthly=pd.read_csv(ex/'monthly_sales.csv',parse_dates=['date'])
    family=pd.read_csv(ex/'family_forecast_metrics.csv');family=family.loc[family.fold.eq(3)&family.method.eq(winner)]
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#F3F6FA','axes.facecolor':'white','axes.labelcolor':'#132C45','text.color':'#132C45','axes.titleweight':'bold'})
    fig,axs=plt.subplots(2,2,figsize=(15,9),layout='constrained')
    axs[0,0].plot(totals.index,totals.sales,color='#132C45',label='Actual');axs[0,0].plot(totals.index,totals.prediction,color='#007F86',label=winner);axs[0,0].legend();axs[0,0].set_title('Final 16-day holdout');axs[0,0].tick_params(axis='x',rotation=25)
    sc=scores.loc[scores.fold.eq(3)].sort_values('WAPE')
    axs[0,1].barh(sc.method,sc.WAPE*100,color=['#007F86' if m==winner else '#AFC4D5' for m in sc.method]);axs[0,1].set_xlabel('Pooled WAPE (%)');axs[0,1].set_title('Out-of-time model comparison')
    top=family.nlargest(7,'WAPE').sort_values('WAPE')
    axs[1,0].barh(top.family,top.WAPE*100,color='#CF8150');axs[1,0].set_xlabel('WAPE (%)');axs[1,0].set_title('Family weaknesses remain visible')
    axs[1,1].plot(inventory.service_z,inventory.fill_rate*100,'o-',color='#007F86');axs[1,1].set_xlabel('Assumed service factor z');axs[1,1].set_ylabel('Simulated fill rate (%)');axs[1,1].set_title('Inventory scenario, not observed savings')
    axs[1,1].set_ylim(99.5,100)
    fig.suptitle('Retail Demand Forecasting and Inventory Analytics',fontsize=19)
    fig.savefig(figures/'project_overview.png',dpi=160);plt.close(fig)
    chart=make_subplots(rows=3,cols=2,subplot_titles=['Historical recorded sales','Final holdout actual versus forecast','Holdout WAPE by model','Selected-model family WAPE','Future forecast (no actuals yet)','Inventory service–stock trade-off'])
    chart.add_trace(go.Scatter(x=monthly.date,y=monthly.Sales,name='Monthly sales',line_color='#132C45'),row=1,col=1)
    for col,color,label in [('sales','#132C45','Holdout actual'),('prediction','#007F86','Holdout forecast')]:chart.add_trace(go.Scatter(x=totals.index,y=totals[col],name=label,line_color=color),row=1,col=2)
    chart.add_trace(go.Bar(x=sc.method,y=sc.WAPE*100,name='Pooled WAPE (%)',marker_color='#007F86'),row=2,col=1)
    chart.add_trace(go.Bar(x=family.family,y=family.WAPE*100,name='Family WAPE (%)',marker_color='#CF8150'),row=2,col=2)
    chart.add_trace(go.Scatter(x=future.index,y=future,name='Future forecast',line_color='#007F86'),row=3,col=1)
    chart.add_trace(go.Scatter(x=inventory.mean_ending_stock,y=inventory.fill_rate*100,text=['z='+str(z) for z in inventory.service_z],mode='markers+lines+text',textposition='top center',name='Scenario fill rate',marker_size=12,line_color='#007F86'),row=3,col=2)
    chart.update_layout(height=1250,paper_bgcolor='#F3F6FA',plot_bgcolor='white',font={'family':'Arial','color':'#132C45'},margin={'l':65,'r':35,'t':60,'b':120},legend={'orientation':'h','y':1.055},template='plotly_white')
    chart.update_xaxes(tickangle=-30,row=2,col=2)
    chart.update_xaxes(title_text='Mean ending stock per family-day (mixed family-specific quantities)',row=3,col=2)
    chart.update_yaxes(title_text='Simulated fill rate (%)',row=3,col=2)
    chart.update_yaxes(range=[99.5,100],row=3,col=2)
    body=chart.to_html(full_html=False,include_plotlyjs=True)
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Retail Demand Forecasting and Inventory Analytics</title><style>body{{margin:0;background:#F3F6FA;font:16px Arial;color:#132C45}}header,main,footer{{max-width:1350px;margin:auto;padding:24px}}header{{background:#132C45;color:white}}h1{{font-size:30px}}.kpis{{display:flex;gap:16px;flex-wrap:wrap}}.kpis div{{padding:18px;background:white;border-radius:10px;min-width:170px}}b{{font-size:27px;color:#007F86}}p{{line-height:1.5}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:10px;border:1px solid #DFE7EF;text-align:left}}</style><header><h1>Retail Demand Forecasting and Inventory Analytics</h1><p>Favorita historical portfolio case study · Python · MySQL · Power BI</p></header><main><section class="kpis"><div><b>{status['sales_rows']:,}</b><br>source sales records</div><div><b>54 / 33</b><br>stores / product families</div><div><b>{status['final_holdout']['WAPE']:.2%}</b><br>final holdout pooled WAPE</div><div><b>{status['final_holdout']['MacroFamilyWAPE']:.2%}</b><br>final holdout macro-family WAPE</div></section><p><strong>Selected model: {html.escape(winner)}.</strong> Winner chosen using two earlier 16-day folds; the final Jul 31–Aug 15, 2017 holdout was excluded from selection. Forecasts operate on national daily family totals, with planned promotions assumed known. Modeling uses the complete Dec 26, 2016–Aug 15, 2017 tail; four missing Christmas dates were not imputed.</p>{body}<h2>Model comparison</h2>{scores.to_html(index=False,float_format=lambda x:f'{x:.5f}')}<h2>Inventory scenarios</h2>{inventory.to_html(index=False,float_format=lambda x:f'{x:,.5f}')}<p>Inventory is a 16-day illustrative lost-sales simulation, not measured operational savings. Lead and review periods are seven days; holding cost is an assumed 0.01 scenario unit per stock unit-day. Sales are recorded quantities, not unconstrained demand or revenue. Different families may use different units. Family errors remain material; no production deployment is claimed.</p></main><footer>Source: Kaggle Store Sales — Time Series Forecasting. Download provenance and hashes: reports/DATA_PROVENANCE.json. Full datasets are excluded from share packages.</footer></html>'''
    (reports/'Interactive_Dashboard.html').write_text(page,encoding='utf-8')
    # Notebook cells are executed here in the same tested Python environment.
    import io,contextlib,traceback
    nb=nbformat.v4.new_notebook();nb.metadata['kernelspec']={'display_name':'Python 3','language':'python','name':'python3'}
    cells=[nbformat.v4.new_markdown_cell('# Retail Demand Forecasting and Inventory Analytics\n\nExecuted review of real pipeline outputs. Run `python src/pipeline.py --source-dir YOUR_FOLDER` and `python src/reporting.py` first. All modeling decisions and limits are documented in the README.'),
    nbformat.v4.new_code_cell("from pathlib import Path\nimport json, pandas as pd\nROOT=Path.cwd()\nif ROOT.name=='notebooks': ROOT=ROOT.parent\nEX=ROOT/'data/exports'\nstatus=json.loads((ROOT/'reports/data_status.json').read_text())\nprint(json.dumps(status,indent=2))"),
    nbformat.v4.new_code_cell("scores=pd.read_csv(EX/'forecast_metrics.csv')\nprint(scores.to_string(index=False))\nprint('Selection folds only:',scores.query('fold<3').groupby('method').MacroFamilyWAPE.mean().idxmin())"),
    nbformat.v4.new_code_cell("folds=pd.read_csv(EX/'fold_dates.csv')\nprint(folds.to_string(index=False))\nprint('Missing calendar dates:',status['missing_calendar_dates'])"),
    nbformat.v4.new_code_cell("family=pd.read_csv(EX/'family_forecast_metrics.csv')\nwinner=status['best_model_selected_on_folds_1_2']\nprint(family.query('fold==3 and method==@winner').sort_values('WAPE',ascending=False).head(10).to_string(index=False))"),
    nbformat.v4.new_code_cell("inventory=pd.read_csv(EX/'inventory_scenarios.csv')\nprint(inventory.to_string(index=False))\nfuture=pd.read_csv(EX/'future_forecast.csv')\nprint('Future rows:',len(future),'Dates:',future.date.min(),future.date.max())"),
    nbformat.v4.new_markdown_cell('## Interpretation\n\nPooled WAPE is weighted by recorded quantities. Macro-family WAPE makes smaller families visible; neither treats kilograms and item counts as economically equivalent. Promotion patterns are associations. Future accuracy is unavailable until actual sales exist. The inventory exercise is a scenario with stated assumptions, not a replenishment recommendation.')]
    import os
    old=Path.cwd();os.chdir(root);env={}
    try:
        count=0
        for cell in cells:
            if cell.cell_type!='code':continue
            count+=1;buf=io.StringIO()
            with contextlib.redirect_stdout(buf):exec(cell.source,env)
            cell.execution_count=count;cell.outputs=[nbformat.v4.new_output('stream',name='stdout',text=buf.getvalue())]
    finally:os.chdir(old)
    nb.cells=cells;nbformat.write(nb,root/'notebooks/01_analysis.ipynb')
    print('Rendered dashboard, overview figure, and five executed notebook cells.')

if __name__=='__main__':run()
