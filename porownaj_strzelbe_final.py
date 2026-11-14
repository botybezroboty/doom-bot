"""Końcowe porównanie obu wersji i dodatkowa niezależna seria kontrolna."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__':
    uruchom_na_ukrytym_pulpicie()
import csv
import json
import statistics
from pathlib import Path
import bot
import bot_przed_poprawka as old
from porownaj_strzelbe import inspect, FIELDS
from sprawdz_wszystko import fresh_seeds

ROOT = Path(__file__).resolve().parent

def main():
    previous = list(csv.DictReader((ROOT / 'porownanie_strzelba_etap.csv').open(encoding='utf-8', newline='')))
    assert len(previous) == 80
    extra = fresh_seeds()
    (ROOT / 'seedy_strzelba_kontrolne.json').write_text(json.dumps(extra, indent=2) + '\n', encoding='utf-8')
    print('Dodatkowe niezależne seedy:', extra, flush=True)
    rows = []
    with (ROOT / 'porownanie_strzelba_final.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        def put(r):
            writer.writerow(r); f.flush(); rows.append(r)
        def play(group, version, seed):
            r = (old if version == 'przed' else bot).run(seed)
            own, selected, exticks = inspect(r)
            result = {'seria':group, 'wersja':version, 'seed':seed, 'seed_silnika':r['seed_silnika'],
                      'wynik':r['wynik'], 'tiki':r['tiki'], 'strzelba':own, 'wybrana_strzelba':selected,
                      'tiki_przy_wyjsciu':exticks, 'powtorka':r['powtorka']}
            put(result)
            print(group, version, seed, r['wynik'], r['tiki'], 'strzelba',own,'wyjście',exticks,flush=True)
        for group in ('dowod', 'nowe'):
            for r in previous:
                if r['seria'] != group or r['wersja'] != 'przed': continue
                put(r)
                play(group, 'po', int(r['seed']))
        for seed, engine in extra:
            play('kontrolne', 'przed', seed)
            play('kontrolne', 'po', seed)
    for group in ('dowod','nowe','kontrolne'):
        for version in ('przed','po'):
            a=[r for r in rows if r['seria']==group and r['wersja']==version]
            wins=[r for r in a if r['wynik']=='wyjscie']
            m=statistics.median(int(r['tiki']) for r in wins) if wins else None
            e=statistics.median(int(r['tiki_przy_wyjsciu']) for r in wins if r['tiki_przy_wyjsciu']!='') if wins else None
            print(group,version,'wyjścia',len(wins),'zgony',sum(r['wynik']=='zgon' for r in a),
                  'limity',sum(r['wynik']=='limit' for r in a),'mediana',m,'strzelby',sum(int(r['strzelba']) for r in a),
                  'wybrane',sum(int(r['wybrana_strzelba']) for r in a),'mediana przy wyjściu',e,flush=True)
if __name__ == '__main__':
    main()
