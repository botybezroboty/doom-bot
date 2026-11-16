"""Pull request check: the bot of a pull request and the bot of master on the same seeds.

The channel Boty bez roboty added this file after the film; the agent from the film
did not write it, and it does not change the bot. It runs bot.py the way a person
does in PowerShell, one seed per call, and counts the results. GitHub Actions uses
it on every pull request (.github/workflows/pr-check.yml). The summary it writes is
in Polish, like the rest of the project's documentation.

The check's seeds are the first SEED_COUNT numbers from 8001 that bot.py accepts
(it rejects those whose engine seed Windows would truncate). Do not tune the bot on
them: tuning uses seeds below 7000, a contributor's own measurement 7001-7100.

    python .github/pr_check.py seeds
    python .github/pr_check.py play --side pr --folder FOLDER --results RESULTS
    python .github/pr_check.py check-all --folder FOLDER --results RESULTS
    python .github/pr_check.py summary --results RESULTS
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FIRST_SEED = 8001
SEED_COUNT = 40
GAME_LIMIT_S = 120  # a game takes 8-20 s on a GitHub machine, a game to the 3500-tic limit about 25 s
CHECK_ALL_LIMIT_S = 15 * 60
MAX_VIDEOS = 5  # videos of lost games per side, kept with the results
SIDES = ('master', 'pr')
SIDE_NAMES = {'master': 'master', 'pr': 'ten pull request'}
# The bot prints "SEED OUTCOME TICS REPLAY". Older versions print the outcome in Polish.
RESULT_LINE = re.compile(r'^(\d+) (wyjscie|zgon|limit|exit|death|timeout) (\d+) (\S+)$')
OUTCOMES = {'wyjscie': 'exit', 'zgon': 'death', 'limit': 'timeout',
            'exit': 'exit', 'death': 'death', 'timeout': 'timeout'}
CHECK_ALL_SCRIPTS = ('check_all.py', 'sprawdz_wszystko.py')  # current name first, the film's name second
CHECK_ALL_LINES = ('defend_the_center aiming', 'defend_the_center random', 'MAP01: exits', 'Median of completed',
                   'defend_the_center celujacy', 'defend_the_center losowy', 'MAP01: wyjścia', 'Mediana ukończonych')
TICS_PER_SECOND = 35


def seed_accepted(seed: int) -> bool:
    """The rule of bot.py: the engine seed must be below 2^31-1."""
    import numpy as np

    engine = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
    return 0 < engine < 2**31 - 1


def check_seeds() -> list[int]:
    seeds, seed = [], FIRST_SEED
    while len(seeds) < SEED_COUNT:
        if seed_accepted(seed):
            seeds.append(seed)
        seed += 1
    return seeds


def child_env() -> dict:
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def tail(text: str, chars: int = 400) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return ' | '.join(lines[-3:])[-chars:] or '(brak komunikatu)'


def kill_tree(proc: subprocess.Popen) -> None:
    # bot.py starts itself a second time on a hidden desktop, so the whole process tree goes.
    if sys.platform == 'win32':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    else:
        proc.kill()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


def read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None


# Games of one side

def play_one(folder: Path, seed: int) -> dict:
    start = time.monotonic()
    proc = subprocess.Popen(
        [sys.executable, 'bot.py', str(seed)], cwd=folder, env=child_env(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
    try:
        out, err = proc.communicate(timeout=GAME_LIMIT_S)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        proc.communicate()
        return {'seed': seed, 'outcome': 'error', 'tics': None, 'replay': None,
                'seconds': round(time.monotonic() - start, 1),
                'note': f'gra trwała dłużej niż {GAME_LIMIT_S} s i została przerwana'}
    seconds = round(time.monotonic() - start, 1)
    for line in reversed(out.splitlines()):
        m = RESULT_LINE.match(line.strip())
        if m and int(m[1]) == seed:
            game = {'seed': seed, 'outcome': OUTCOMES[m[2]], 'tics': int(m[3]), 'replay': m[4], 'seconds': seconds}
            if proc.returncode != 0:
                game['note'] = f'gra skończona ({m[2]}), ale bot.py zakończył się kodem {proc.returncode}: {tail(err)}'
                game['outcome'] = 'error'
            return game
    return {'seed': seed, 'outcome': 'error', 'tics': None, 'replay': None, 'seconds': seconds,
            'note': f'bot.py zakończył się kodem {proc.returncode} bez linii wyniku: {tail(err or out)}'}


def replay_folder(folder: Path) -> Path:
    for name in ('replays', 'powtorki'):  # current name first, the film's name second
        if (folder / name).is_dir():
            return folder / name
    return folder / 'replays'


def play(args: argparse.Namespace) -> int:
    folder = Path(args.folder).resolve()
    results = Path(args.results).resolve()
    (results / 'videos').mkdir(parents=True, exist_ok=True)
    out_file = results / f'{args.side}.jsonl'
    out_file.unlink(missing_ok=True)
    seeds = check_seeds()
    # A game is two processes, Python and the engine, which hand the CPU to each other every
    # tic. On a GitHub machine with 2 CPUs two games at once ran slower than one after another.
    parallel = args.parallel or max(1, (os.cpu_count() or 2) // 2)
    print(f'{args.side}: {len(seeds)} seedów ({seeds[0]}-{seeds[-1]}), gry po {parallel} naraz', flush=True)
    start = time.monotonic()
    lock = threading.Lock()
    videos = 0

    def one(seed: int) -> dict:
        nonlocal videos
        game = play_one(folder, seed)
        with lock:
            with out_file.open('a', encoding='utf-8') as f:
                f.write(json.dumps(game, ensure_ascii=False) + '\n')
            video = replay_folder(folder) / f'{game["replay"]}.mp4'
            if game['outcome'] in ('death', 'timeout') and videos < MAX_VIDEOS and video.is_file():
                shutil.copyfile(video, results / 'videos' / f'{args.side}_{seed}_{game["outcome"]}.mp4')
                videos += 1
            tics = game['tics'] if game['tics'] is not None else '-'
            print(f'{seed} {game["outcome"]:7} {tics:>5} {game["seconds"]:6.1f} s'
                  + (f'  {game["note"]}' if game.get('note') else ''), flush=True)
        return game

    with ThreadPoolExecutor(parallel) as pool:
        games = list(pool.map(one, seeds))
    seconds = round(time.monotonic() - start, 1)
    write_json(results / f'run_{args.side}.json', {
        'seeds': seeds, 'parallel': parallel, 'cpus': os.cpu_count(), 'seconds': seconds})
    errors = sum(g['outcome'] == 'error' for g in games)
    print(f'{args.side}: {len(games)} gier w {seconds} s, błędów {errors}', flush=True)
    return 1 if errors else 0


# The project's own check script (check_all.py, in the film sprawdz_wszystko.py)

def check_all(args: argparse.Namespace) -> int:
    folder = Path(args.folder).resolve()
    results = Path(args.results).resolve()
    results.mkdir(parents=True, exist_ok=True)
    script = next((s for s in CHECK_ALL_SCRIPTS if (folder / s).is_file()), CHECK_ALL_SCRIPTS[0])
    start = time.monotonic()
    note = None
    with (results / 'check_all.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([sys.executable, script], cwd=folder, env=child_env(),
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            code = proc.wait(timeout=CHECK_ALL_LIMIT_S)
        except subprocess.TimeoutExpired:
            kill_tree(proc)
            proc.wait()
            code, note = None, f'przerwany po {CHECK_ALL_LIMIT_S // 60} min'
    seconds = round(time.monotonic() - start, 1)
    write_json(results / 'check_all.json', {'script': script, 'code': code, 'seconds': seconds, 'note': note,
                                            'cpus': os.cpu_count()})
    print((results / 'check_all.log').read_text(encoding='utf-8', errors='replace'), flush=True)
    print(f'{script}: kod {code} po {seconds} s', flush=True)
    return 0 if code == 0 else 1


# Summary (in Polish: the owner and contributors read it)

def read_games(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def sign_test_p(a: int, b: int) -> float:
    """Exact two-sided sign test: how easily coin tosses split a:b."""
    n, k = a + b, min(a, b)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def number(x: float, digits: int = 1) -> str:
    return f'{x:.{digits}f}'.replace('.', ',')


def p_text(p: float) -> str:
    return 'p < 0,001' if p < 0.001 else f'p = {number(p, 3)}'


def duration(seconds: float | None) -> str:
    if seconds is None:
        return '?'
    m, s = divmod(round(seconds), 60)
    return f'{m} min {s} s' if m else f'{s} s'


def tics_text(t: float | None) -> str:
    if t is None:
        return '-'
    return f'{t:g} ({number(t / TICS_PER_SECOND)} s)'


def stats(games: list[dict]) -> dict:
    exits = [g['tics'] for g in games if g['outcome'] == 'exit']
    st = {k: sum(g['outcome'] == k for g in games) for k in ('exit', 'death', 'timeout', 'error')}
    st['games'] = len(games)
    st['median'] = statistics.median(exits) if exits else None
    return st


def game_text(g: dict | None) -> str:
    if g is None:
        return 'brak'
    if g['outcome'] == 'error':
        return 'błąd'
    name = {'exit': 'wyjście', 'death': 'zgon', 'timeout': 'limit czasu'}[g['outcome']]
    return f'{name}, {g["tics"]}'


def verdict(master: dict, pr: dict) -> tuple[str, list[str], bool]:
    """Returns the verdict, the lines that explain it, and whether the pull request breaks something."""
    common = sorted(set(master) & set(pr))
    lines = []
    errors = sum(pr[s]['outcome'] == 'error' for s in pr)
    if errors:
        return f'Błąd: {errors} gier z tego pull requestu nie skończyło się wynikiem', lines, True
    better = sum(pr[s]['outcome'] == 'exit' and master[s]['outcome'] != 'exit' for s in common)
    worse = sum(master[s]['outcome'] == 'exit' and pr[s]['outcome'] != 'exit' for s in common)
    p_exits = sign_test_p(better, worse)
    both = [s for s in common if pr[s]['outcome'] == master[s]['outcome'] == 'exit']
    faster = sum(pr[s]['tics'] < master[s]['tics'] for s in both)
    slower = sum(pr[s]['tics'] > master[s]['tics'] for s in both)
    p_time = sign_test_p(faster, slower)
    different = [s for s in common if (pr[s]['outcome'], pr[s]['tics']) != (master[s]['outcome'], master[s]['tics'])]

    if better or worse:
        sure = 'raczej nie przypadek' if p_exits < 0.05 else 'to może być przypadek'
        lines.append(f'Wyjścia: ten pull request wychodzi tam, gdzie master nie, na {better} seedach, '
                     f'a master tam, gdzie on nie, na {worse} ({sure}: {p_text(p_exits)} w teście znaków).')
    else:
        lines.append('Wyjścia: w obu wersjach wyjściem kończą się te same seedy.')
    if both and (faster or slower):
        diffs = [pr[s]['tics'] - master[s]['tics'] for s in both]
        sure = 'raczej nie przypadek' if p_time < 0.05 else 'to może być przypadek'
        lines.append(f'Czas na {len(both)} seedach z wyjściem w obu wersjach: szybciej na {faster}, wolniej na {slower}, '
                     f'tak samo na {len(both) - faster - slower}; mediana różnicy {statistics.median(diffs):+g} tików '
                     f'({sure}: {p_text(p_time)}).')

    if not different:
        return f'Bez zmian: na wszystkich {len(common)} seedach ten sam wynik i ta sama liczba tików co master', lines, False
    if worse > better and p_exits < 0.05:
        return f'Gorzej: {worse - better} wyjść mniej niż master na {len(common)} seedach', lines, True
    if better > worse and p_exits < 0.05:
        return f'Lepiej: {better - worse} wyjść więcej niż master na {len(common)} seedach', lines, False
    if p_time < 0.05 and (faster or slower):
        direction = 'Szybciej' if faster > slower else 'Wolniej'
        exits = 'przy tych samych wyjściach' if not (better or worse) else 'przy liczbie wyjść bez pewnej różnicy'
        return f'{direction} niż master {exits}', lines, False
    return f'Bez pewnej różnicy na {len(common)} seedach', lines, False


def summary(args: argparse.Namespace) -> int:
    results = Path(args.results)
    games = {s: read_games(results / f'{s}.jsonl') for s in SIDES}
    by_seed = {s: {g['seed']: g for g in games[s]} for s in SIDES}
    st = {s: stats(games[s]) for s in SIDES}
    runs = {s: read_json(results / f'run_{s}.json') for s in SIDES}
    seeds = next((r['seeds'] for r in runs.values() if r), [])
    ca = read_json(results / 'check_all.json')
    ca_name = ca['script'] if ca else CHECK_ALL_SCRIPTS[0]
    log = results / 'check_all.log'
    log_text = log.read_text(encoding='utf-8', errors='replace') if log.is_file() else ''
    ca_ok = bool(ca) and ca['code'] == 0
    changed = []
    if args.changed_files and Path(args.changed_files).is_file():
        changed = [c.strip() for c in Path(args.changed_files).read_text(encoding='utf-8').splitlines() if c.strip()]

    out = [f'## Sprawdzenie bota: pull request{f" #{args.number}" if args.number else ""} i master\n']
    if games['pr'] and games['master']:
        text, lines, breaks = verdict(by_seed['master'], by_seed['pr'])
        if st['master']['error']:
            text += f'; uwaga: {st["master"]["error"]} gier master też nie skończyło się wynikiem'
            breaks = True
    else:
        text, lines, breaks = 'Brak wyników gier, zobacz log zadań z grami', [], True
    if not ca_ok:
        text += f'; {ca_name} nie przeszedł'
    out.append(f'**{text}.**\n')
    out.append('| Wersja | Gier | Wyjścia | Zgony | Limity czasu | Błędy | Mediana tików wyjść |')
    out.append('|---|---:|---:|---:|---:|---:|---:|')
    for s in SIDES:
        x = st[s]
        sha = getattr(args, f'{s}_sha')
        name = SIDE_NAMES[s] + (f' `{sha[:7]}`' if sha else '')
        out.append(f'| {name} | {x["games"]} | {x["exit"]} | {x["death"]} | {x["timeout"]} | {x["error"]} | {tics_text(x["median"])} |')
    out.append('')
    out.extend(f'- {line}' for line in lines)
    if lines:
        out.append('')

    other = [s for s in seeds if (by_seed['pr'].get(s) or {}).get('outcome') != (by_seed['master'].get(s) or {}).get('outcome')]
    if other:
        out.append('Seedy z innym wynikiem (wynik, tiki):\n')
        out.append('| Seed | master | ten pull request |')
        out.append('|---:|---|---|')
        for s in other[:20]:
            out.append(f'| {s} | {game_text(by_seed["master"].get(s))} | {game_text(by_seed["pr"].get(s))} |')
        if len(other) > 20:
            out.append(f'| … | i {len(other) - 20} kolejnych | |')
        out.append('')
    errors = [(s, g) for s in SIDES for g in games[s] if g['outcome'] == 'error']
    out.extend(f'- Błąd ({SIDE_NAMES[s]}, seed {g["seed"]}): {g.get("note", "")}' for s, g in errors[:5])
    if errors:
        out.append('')

    out.append(f'### {ca_name}\n')
    if ca is None:
        out.append('Brak wyniku: nie uruchomił się albo jego zadanie przerwano.')
    elif ca_ok:
        out.append(f'Przeszedł ({duration(ca["seconds"])}).')
    else:
        reason = ca.get('note') or f'kod wyjścia {ca["code"]}'
        out.append(f'**Nie przeszedł** ({reason}, po {duration(ca["seconds"])}). Koniec logu: `{tail(log_text, 600)}`')
    out.extend(f'- {line.strip()}' for line in log_text.splitlines() if line.startswith(CHECK_ALL_LINES))
    out.append('')

    out.append('### Jak to liczono\n')
    if seeds:
        out.append(f'- Seedy: {len(seeds)} pierwszych od {FIRST_SEED}, które bot.py przyjmuje ({seeds[0]}-{seeds[-1]}), '
                   'te same przy każdym pull requeście. Każda gra to osobne `python bot.py SEED`, jak w CONTRIBUTING.md.')
    times = []
    for s in SIDES:
        if runs[s] and games[s]:
            mean = statistics.mean(g['seconds'] for g in games[s])
            times.append(f'{SIDE_NAMES[s]} {duration(runs[s]["seconds"])} (gra średnio {number(mean)} s, '
                         f'po {runs[s]["parallel"]} naraz na {runs[s]["cpus"]} procesorach)')
    if ca:
        times.append(f'{ca_name} {duration(ca["seconds"])}')
    if times:
        out.append(f'- Każda część na osobnej maszynie GitHuba z Windowsem: {"; ".join(times)}.')
    out.append('- Ten sam seed i ten sam kod dają tę samą grę co do tiku, więc każda różnica w tabeli wynika ze zmiany w kodzie.')
    out.append(f'- Pełne wyniki, log {ca_name} i filmy z kilku przegranych gier: artefakty `results-*` na dole strony tego uruchomienia.')
    if changed:
        rest = f' i {len(changed) - 15} innych' if len(changed) > 15 else ''
        out.append(f'- Zmienione pliki: {", ".join(f"`{c}`" for c in changed[:15])}{rest}.')
    check_files = [c for c in changed if c.startswith('.github/') and not c.startswith('.github/ISSUE_TEMPLATE/')]
    if check_files:
        out.append('')
        out.append(f'> **Uwaga:** ten pull request zmienia pliki samego sprawdzenia ({", ".join(f"`{c}`" for c in check_files)}). '
                   'Liczby wyżej policzył kod z tego pull requestu, więc przeczytaj te zmiany, zanim im uwierzysz.')
    if 'requirements.txt' in changed:
        out.append('')
        out.append('> Ten pull request zmienia `requirements.txt`: obie wersje grały na paczkach z tego pull requestu.')

    md = '\n'.join(out) + '\n'
    print(md)
    # Red: something breaks. A slower bot with the same exits only gets a warning: a change may
    # buy reliability with time, and master exits on nearly all of these seeds, so a gain in
    # exits cannot show here.
    fail = breaks or not ca_ok
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(md)
        level = 'warning' if fail or text.startswith('Wolniej') else 'notice'
        print(f'::{level} title=Sprawdzenie bota::{text}.')
    return 1 if fail else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('seeds', help='print the check seeds')
    p = sub.add_parser('play', help='play one side of the comparison on the check seeds')
    p.add_argument('--side', choices=SIDES, required=True)
    p.add_argument('--folder', required=True, help='folder with that side\'s code')
    p.add_argument('--results', required=True)
    p.add_argument('--parallel', type=int, help='games at once (default: half the CPUs)')
    p = sub.add_parser('check-all', help='run the project\'s own check script')
    p.add_argument('--folder', required=True)
    p.add_argument('--results', required=True)
    p = sub.add_parser('summary', help='the table of results, in Polish')
    p.add_argument('--results', required=True)
    p.add_argument('--number', help='pull request number')
    p.add_argument('--pr-sha', dest='pr_sha')
    p.add_argument('--master-sha', dest='master_sha')
    p.add_argument('--changed-files', dest='changed_files', help='file listing the changed files, one per line')
    args = parser.parse_args()
    if args.command == 'seeds':
        print(' '.join(map(str, check_seeds())))
        return 0
    return {'play': play, 'check-all': check_all, 'summary': summary}[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
