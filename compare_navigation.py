"""Comparison on 60 known and 20 new MAP01 seeds."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__': run_on_hidden_desktop()
import csv
import json
import math
import statistics
from pathlib import Path
import bot
import bot_before_navigation as old
from check_all import check_artifacts, verify_exit

ROOT=Path(__file__).resolve().parent
REPLAYS=ROOT/'replays'
FIELDS=['set','version','seed','engine_seed','outcome','tics','shotgun','pickup_at_ledge','pickup_distance','tics_at_exit','replay']


def inspect(group, version, row, validate_exit=False):
    path=REPLAYS/(row['replay']+'.lmp')
    check_artifacts(path,int(row['engine_seed']))
    log=[json.loads(x) for x in path.with_suffix('.jsonl').read_text(encoding='utf-8').splitlines()]
    ticks=[q for q in log if q.get('type')=='tic']
    end=log[-1]
    if end['outcome']!=row['outcome'] or int(end['tic'])!=int(row['tics']):
        raise RuntimeError(f'Log does not match {path}')
    if validate_exit and row['outcome']=='exit':
        verify_exit({**row,'tics':int(row['tics'])})
    got=any(q.get('shotgun',0)>0 for q in ticks)
    pickup=next((q for q in ticks if q.get('shotgun',0)>0),None)
    distance=round(math.hypot(pickup['x']-1536,pickup['y']+160),1) if pickup else ''
    near=int(pickup is not None and distance<=40)
    exit_ticks=''
    if row['outcome']=='exit':
        last=len(log[0]['route'])-1
        first=next((q['tic'] for q in ticks if q['waypoint']==last),None)
        if first is not None: exit_ticks=int(row['tics'])-first+1
    return dict(set=group,version=version,seed=row['seed'],engine_seed=row['engine_seed'],outcome=row['outcome'],tics=row['tics'],shotgun=int(got),pickup_at_ledge=near,pickup_distance=distance,tics_at_exit=exit_ticks,replay=row['replay'])


def main():
    previous=list(csv.DictReader((ROOT/'comparison_shotgun_final.csv').open(encoding='utf-8',newline='')))
    previous=[r for r in previous if r['version']=='after']
    extra=json.loads((ROOT/'seeds_navigation_control.json').read_text(encoding='utf-8'))
    if len(previous)!=60 or len({r['engine_seed'] for r in previous})!=60 or len(extra)!=20:
        raise ValueError('Wrong seed sets')
    if {int(r['engine_seed']) for r in previous}&{engine for seed,engine in extra}:
        raise ValueError('Repeated engine seeds')
    rows=[]
    with (ROOT/'comparison_navigation.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        def put(r):
            writer.writerow(r);f.flush();rows.append(r)
            print(r['set'],r['version'],r['seed'],r['outcome'],r['tics'],'shotgun at ledge',r['pickup_at_ledge'],flush=True)
        for r in previous:
            put(inspect(r['set'],'before',r))
            new=bot.run(int(r['seed']))
            put(inspect(r['set'],'after',new,True))
        for seed,engine in extra:
            r=old.run(seed);put(inspect('new_control','before',r,True))
            r=bot.run(seed);put(inspect('new_control','after',r,True))
    for group in ('proof','new','control','new_control'):
        for version in ('before','after'):
            a=[r for r in rows if r['set']==group and r['version']==version]
            wins=[r for r in a if r['outcome']=='exit']
            print(group,version,'exits',len(wins),'deaths',sum(r['outcome']=='death' for r in a),
                  'timeouts',sum(r['outcome']=='timeout' for r in a),'median',statistics.median(int(r['tics']) for r in wins) if wins else None,
                  'shotgun',sum(r['shotgun'] for r in a),'at ledge',sum(r['pickup_at_ledge'] for r in a),flush=True)

if __name__=='__main__': main()
