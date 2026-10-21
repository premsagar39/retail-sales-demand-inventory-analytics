"""Load only generated project CSVs into a dedicated MySQL database."""
from pathlib import Path
import argparse, csv, json, os, re
import pandas as pd
from sqlalchemy import create_engine

ROOT=Path(__file__).resolve().parents[1]

def connect(url=None):
    url=url or os.environ.get('DATABASE_URL')
    if not url:raise ValueError('Set DATABASE_URL using .env.example. Credentials are never committed.')
    engine=create_engine(url,connect_args={'local_infile':True},pool_pre_ping=True)
    return engine,engine.raw_connection()

def load(root=ROOT,url=None):
    """Create empty tables, load dimensions before facts, and run all business queries."""
    root=Path(root);engine,connection=connect(url)
    schema=json.loads((root/'src/schema.json').read_text())
    try:
        cur=connection.cursor()
        for sql in (root/'sql/schema.sql').read_text().split(';'):
            if sql.strip():cur.execute(sql)
        for table,cols in schema.items():
            cur.execute(f'SELECT COUNT(*) FROM `{table}`')
            if cur.fetchone()[0]:raise ValueError(f'{table} is not empty; use a fresh project database for repeatable loads')
            source=root/'data/processed'/(table+'.csv')
            if not source.is_file():raise FileNotFoundError(source)
            with source.open(encoding='utf-8-sig',newline='') as f:header=next(csv.reader(f))
            if set(header)!=set(cols):raise ValueError(f'CSV/schema mismatch: {table}')
            variables=','.join('@v'+str(i) for i in range(len(header)))
            assignments=','.join(f'`{c}`=NULLIF(@v{i},\'\')' for i,c in enumerate(header))
            with source.open('rb') as f:terminator='\r\n' if b'\r\n' in f.read(4096) else '\n'
            statement=f'''LOAD DATA LOCAL INFILE %s INTO TABLE `{table}` CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"' LINES TERMINATED BY %s IGNORE 1 LINES ({variables}) SET {assignments}'''
            cur.execute(statement,(source.resolve().as_posix(),terminator))
            cur.execute('SHOW COUNT(*) WARNINGS');warnings=cur.fetchone()[0]
            if warnings:
                cur.execute('SHOW WARNINGS LIMIT 4')
                raise ValueError(f'{table} load has {warnings} warnings: {cur.fetchall()}')
            connection.commit()
            cur.execute(f'SELECT COUNT(*) FROM `{table}`');print(table,cur.fetchone()[0],flush=True)
        results={}
        report=root/'reports/sql_results';report.mkdir(parents=True,exist_ok=True)
        query_text='\n'.join(line for line in (root/'sql/analysis_queries.sql').read_text().splitlines() if not line.lstrip().startswith('--'))
        for number,query in enumerate(query_text.split(';'),1):
            if not query.strip():continue
            cur.execute(query);rows=cur.fetchall();names=[c[0] for c in cur.description]
            df=pd.DataFrame(rows,columns=names);df.to_csv(report/f'q{number:02d}.csv',index=False)
            results[f'Q{number:02d}']={'rows':len(df),'columns':names}
        (root/'reports/sql_execution.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        return results
    finally:connection.close();engine.dispose()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database-url',default=None,help='Prefer DATABASE_URL environment variable');a=p.parse_args();load(url=a.database_url)
