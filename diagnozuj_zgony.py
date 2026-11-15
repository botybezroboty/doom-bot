"""Zestawienie obrażeń w dziewięciu dawnych zgonach, bez nowych gier."""
import csv
import json
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parent
BARRELS = [(872,40),(912,24),(864,88),(1264,-224),(1240,-72),(704,-688)]

def main():
    result = []
    for row in csv.DictReader((ROOT/'porownanie_nawigacja.csv').open(encoding='utf-8')):
        if row['wersja'] != 'po' or row['wynik'] != 'zgon':
            continue
        path = ROOT/'powtorki'/(row['powtorka']+'.jsonl')
        log = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        ticks = log[1:-1]
        damage = []
        for before, after in zip(ticks, ticks[1:]+[log[-1]]):
            loss = before['zycie'] - after['zycie']
            if loss >= 25:
                nearest = min(BARRELS, key=lambda p: math.dist(p,(before['x'],before['y'])))
                damage.append(dict(tik=before['tik'],x=round(before['x'],1),y=round(before['y'],1),
                                   utrata_zycia=loss,zycie_po=after['zycie'],beczka=nearest,
                                   odleglosc=round(math.dist(nearest,(before['x'],before['y'])),1)))
        result.append(dict(seed=int(row['seed']),powtorka=row['powtorka'],zgon=int(row['tiki']),obrazenia=damage))
    (ROOT/'diagnoza_niezawodnosc.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Zdiagnozowane zgony:',len(result))

if __name__ == '__main__': main()
