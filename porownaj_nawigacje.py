"""Porównanie na 60 znanych i 20 nowych seedach MAP01."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__': uruchom_na_ukrytym_pulpicie()
import csv
import json
import math
import statistics
from pathlib import Path
import bot
import bot_przed_nawigacja as old
from sprawdz_wszystko import check_artifacts, verify_exit

ROOT=Path(__file__).resolve().parent
REPLAYS=ROOT/'powtorki'
FIELDS=['seria','wersja','seed','seed_silnika','wynik','tiki','strzelba','zdobycie_przy_podwyzszeniu','odleglosc_zdobycia','tiki_przy_wyjsciu','powtorka']


def inspect(group, version, row, validate_exit=False):
    path=REPLAYS/(row['powtorka']+'.lmp')
    check_artifacts(path,int(row['seed_silnika']))
    log=[json.loads(x) for x in path.with_suffix('.jsonl').read_text(encoding='utf-8').splitlines()]
    ticks=[q for q in log if q.get('typ')=='tik']
    end=log[-1]
    if end['wynik']!=row['wynik'] or int(end['tik'])!=int(row['tiki']):
        raise RuntimeError(f'Niezgodny dziennik {path}')
    if validate_exit and row['wynik']=='wyjscie':
        verify_exit({**row,'tiki':int(row['tiki'])})
    got=any(q.get('strzelba',0)>0 for q in ticks)
    pickup=next((q for q in ticks if q.get('strzelba',0)>0),None)
    distance=round(math.hypot(pickup['x']-1536,pickup['y']+160),1) if pickup else ''
    near=int(pickup is not None and distance<=40)
    exit_ticks=''
    if row['wynik']=='wyjscie':
        last=len(log[0]['trasa'])-1
        first=next((q['tik'] for q in ticks if q['cel']==last),None)
        if first is not None: exit_ticks=int(row['tiki'])-first+1
    return dict(seria=group,wersja=version,seed=row['seed'],seed_silnika=row['seed_silnika'],wynik=row['wynik'],tiki=row['tiki'],strzelba=int(got),zdobycie_przy_podwyzszeniu=near,odleglosc_zdobycia=distance,tiki_przy_wyjsciu=exit_ticks,powtorka=row['powtorka'])


def main():
    previous=list(csv.DictReader((ROOT/'porownanie_strzelba_final.csv').open(encoding='utf-8',newline='')))
    previous=[r for r in previous if r['wersja']=='po']
    extra=json.loads((ROOT/'seedy_nawigacja_kontrolne.json').read_text(encoding='utf-8'))
    if len(previous)!=60 or len({r['seed_silnika'] for r in previous})!=60 or len(extra)!=20:
        raise ValueError('Niewłaściwe zestawy seedów')
    if {int(r['seed_silnika']) for r in previous}&{engine for seed,engine in extra}:
        raise ValueError('Powtórzone seedy silnika')
    rows=[]
    with (ROOT/'porownanie_nawigacja.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        def put(r):
            writer.writerow(r);f.flush();rows.append(r)
            print(r['seria'],r['wersja'],r['seed'],r['wynik'],r['tiki'],'strzelba przy podwyższeniu',r['zdobycie_przy_podwyzszeniu'],flush=True)
        for r in previous:
            put(inspect(r['seria'],'przed',r))
            new=bot.run(int(r['seed']))
            put(inspect(r['seria'],'po',new,True))
        for seed,engine in extra:
            r=old.run(seed);put(inspect('nowe_kontrolne','przed',r,True))
            r=bot.run(seed);put(inspect('nowe_kontrolne','po',r,True))
    for group in ('dowod','nowe','kontrolne','nowe_kontrolne'):
        for version in ('przed','po'):
            a=[r for r in rows if r['seria']==group and r['wersja']==version]
            wins=[r for r in a if r['wynik']=='wyjscie']
            print(group,version,'wyjścia',len(wins),'zgony',sum(r['wynik']=='zgon' for r in a),
                  'limity',sum(r['wynik']=='limit' for r in a),'mediana',statistics.median(int(r['tiki']) for r in wins) if wins else None,
                  'strzelba',sum(r['strzelba'] for r in a),'przy podwyższeniu',sum(r['zdobycie_przy_podwyzszeniu'] for r in a),flush=True)

if __name__=='__main__': main()
