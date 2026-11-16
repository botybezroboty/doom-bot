"""A list of the damage in nine earlier deaths, without new games."""
import csv
import json
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parent
BARRELS = [(872,40),(912,24),(864,88),(1264,-224),(1240,-72),(704,-688)]

def main():
    result = []
    for row in csv.DictReader((ROOT/'comparison_navigation.csv').open(encoding='utf-8')):
        if row['version'] != 'after' or row['outcome'] != 'death':
            continue
        path = ROOT/'replays'/(row['replay']+'.jsonl')
        log = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        ticks = log[1:-1]
        damage = []
        for before, after in zip(ticks, ticks[1:]+[log[-1]]):
            loss = before['health'] - after['health']
            if loss >= 25:
                nearest = min(BARRELS, key=lambda p: math.dist(p,(before['x'],before['y'])))
                damage.append(dict(tic=before['tic'],x=round(before['x'],1),y=round(before['y'],1),
                                   health_lost=loss,health_after=after['health'],barrel=nearest,
                                   distance=round(math.dist(nearest,(before['x'],before['y'])),1)))
        result.append(dict(seed=int(row['seed']),replay=row['replay'],death=int(row['tics']),damage=damage))
    (ROOT/'reliability_diagnosis.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Deaths diagnosed:',len(result))

if __name__ == '__main__': main()
