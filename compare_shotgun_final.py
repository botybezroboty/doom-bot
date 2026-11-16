"""Final comparison of both versions and an extra independent control set."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__':
    run_on_hidden_desktop()
import csv
import json
import statistics
from pathlib import Path
import bot
import bot_before_fix as old
from compare_shotgun import inspect, FIELDS
from check_all import fresh_seeds

ROOT = Path(__file__).resolve().parent

def main():
    previous = list(csv.DictReader((ROOT / 'comparison_shotgun_stage.csv').open(encoding='utf-8', newline='')))
    assert len(previous) == 80
    extra = fresh_seeds()
    (ROOT / 'seeds_shotgun_control.json').write_text(json.dumps(extra, indent=2) + '\n', encoding='utf-8')
    print('Extra independent seeds:', extra, flush=True)
    rows = []
    with (ROOT / 'comparison_shotgun_final.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        def put(r):
            writer.writerow(r); f.flush(); rows.append(r)
        def play(group, version, seed):
            r = (old if version == 'before' else bot).run(seed)
            own, selected, exticks = inspect(r)
            result = {'set':group, 'version':version, 'seed':seed, 'engine_seed':r['engine_seed'],
                      'outcome':r['outcome'], 'tics':r['tics'], 'shotgun':own, 'shotgun_selected':selected,
                      'tics_at_exit':exticks, 'replay':r['replay']}
            put(result)
            print(group, version, seed, r['outcome'], r['tics'], 'shotgun',own,'exit',exticks,flush=True)
        for group in ('proof', 'new'):
            for r in previous:
                if r['set'] != group or r['version'] != 'before': continue
                put(r)
                play(group, 'after', int(r['seed']))
        for seed, engine in extra:
            play('control', 'before', seed)
            play('control', 'after', seed)
    for group in ('proof','new','control'):
        for version in ('before','after'):
            a=[r for r in rows if r['set']==group and r['version']==version]
            wins=[r for r in a if r['outcome']=='exit']
            m=statistics.median(int(r['tics']) for r in wins) if wins else None
            e=statistics.median(int(r['tics_at_exit']) for r in wins if r['tics_at_exit']!='') if wins else None
            print(group,version,'exits',len(wins),'deaths',sum(r['outcome']=='death' for r in a),
                  'timeouts',sum(r['outcome']=='timeout' for r in a),'median',m,'shotguns',sum(int(r['shotgun']) for r in a),
                  'selected',sum(int(r['shotgun_selected']) for r in a),'median at exit',e,flush=True)
if __name__ == '__main__':
    main()
