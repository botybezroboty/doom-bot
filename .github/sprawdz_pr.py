"""Sprawdzenie pull requestu: bot z pull requestu i bot z master na tych samych seedach.

Ten plik dodał kanał Boty bez roboty po filmie. Nie napisał go agent z filmu
i nie zmienia on bota: uruchamia bot.py tak samo, jak robisz to w PowerShellu,
po jednym seedzie na wywołanie, i liczy wyniki. Używa go GitHub Actions
(.github/workflows/sprawdzenie.yml) przy każdym pull requeście.

Seedy sprawdzenia to pierwsze LICZBA_SEEDOW numerów od 8001, które bot.py
przyjmuje (odrzuca te, przy których Windows obciąłby seed silnika). Nie strój
na nich bota: do strojenia są seedy poniżej 7000, do własnego pomiaru 7001-7100.

    python .github/sprawdz_pr.py seedy
    python .github/sprawdz_pr.py graj --wersja pr --folder FOLDER --wyniki WYNIKI
    python .github/sprawdz_pr.py sprawdz --folder FOLDER --wyniki WYNIKI
    python .github/sprawdz_pr.py podsumuj --wyniki WYNIKI
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

PIERWSZY_SEED = 8001
LICZBA_SEEDOW = 40
LIMIT_GRY_S = 120  # gra trwa na maszynie GitHuba 10-13 s, gra do limitu 3500 tików około 20 s
LIMIT_SPRAWDZ_S = 15 * 60
MAKS_FILMOW = 5  # filmy z przegranych gier jednej wersji, dołączane do wyników
WERSJE = ('master', 'pr')
NAZWY = {'master': 'master', 'pr': 'ten pull request'}
LINIA = re.compile(r'^(\d+) (wyjscie|zgon|limit) (\d+) (\S+)$')
TIKI_NA_SEKUNDE = 35


def seed_przyjety(seed: int) -> bool:
    """Ta sama reguła co w bot.py: seed silnika musi być mniejszy niż 2^31-1."""
    import numpy as np

    silnik = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
    return 0 < silnik < 2**31 - 1


def seedy() -> list[int]:
    lista, seed = [], PIERWSZY_SEED
    while len(lista) < LICZBA_SEEDOW:
        if seed_przyjety(seed):
            lista.append(seed)
        seed += 1
    return lista


def srodowisko() -> dict:
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def koncowka(tekst: str, znakow: int = 400) -> str:
    linie = [linia.strip() for linia in tekst.splitlines() if linia.strip()]
    return ' | '.join(linie[-3:])[-znakow:] or '(brak komunikatu)'


def zabij(proc: subprocess.Popen) -> None:
    # bot.py uruchamia się drugi raz na ukrytym pulpicie, więc kończymy całe drzewo procesów.
    if sys.platform == 'win32':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    else:
        proc.kill()


def zapisz_json(sciezka: Path, dane: dict) -> None:
    sciezka.write_text(json.dumps(dane, ensure_ascii=False), encoding='utf-8')


def czytaj_json(sciezka: Path) -> dict | None:
    return json.loads(sciezka.read_text(encoding='utf-8')) if sciezka.is_file() else None


# Gry jednej wersji

def zagraj(folder: Path, seed: int) -> dict:
    start = time.monotonic()
    proc = subprocess.Popen(
        [sys.executable, 'bot.py', str(seed)], cwd=folder, env=srodowisko(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
    try:
        out, err = proc.communicate(timeout=LIMIT_GRY_S)
    except subprocess.TimeoutExpired:
        zabij(proc)
        proc.communicate()
        return {'seed': seed, 'wynik': 'blad', 'tiki': None, 'powtorka': None,
                'czas_s': round(time.monotonic() - start, 1),
                'opis': f'gra trwała dłużej niż {LIMIT_GRY_S} s i została przerwana'}
    czas = round(time.monotonic() - start, 1)
    for linia in reversed(out.splitlines()):
        m = LINIA.match(linia.strip())
        if m and int(m[1]) == seed:
            wynik = {'seed': seed, 'wynik': m[2], 'tiki': int(m[3]), 'powtorka': m[4], 'czas_s': czas}
            if proc.returncode != 0:
                wynik['opis'] = f'gra skończona ({m[2]}), ale bot.py zakończył się kodem {proc.returncode}: {koncowka(err)}'
                wynik['wynik'] = 'blad'
            return wynik
    return {'seed': seed, 'wynik': 'blad', 'tiki': None, 'powtorka': None, 'czas_s': czas,
            'opis': f'bot.py zakończył się kodem {proc.returncode} bez linii wyniku: {koncowka(err or out)}'}


def graj(args: argparse.Namespace) -> int:
    folder = Path(args.folder).resolve()
    wyniki = Path(args.wyniki).resolve()
    (wyniki / 'filmy').mkdir(parents=True, exist_ok=True)
    plik = wyniki / f'{args.wersja}.jsonl'
    plik.unlink(missing_ok=True)
    lista = seedy()
    # Gra to dwa procesy, Python i silnik, które oddają sobie procesor co tik. Na runnerze
    # z 2 procesorami dwie gry naraz szły wolniej niż jedna po drugiej.
    rownolegle = args.rownolegle or max(1, (os.cpu_count() or 2) // 2)
    print(f'{args.wersja}: {len(lista)} seedów ({lista[0]}-{lista[-1]}), gry po {rownolegle} naraz', flush=True)
    start = time.monotonic()
    zamek = threading.Lock()
    filmy = 0

    def jedna(seed: int) -> dict:
        nonlocal filmy
        gra = zagraj(folder, seed)
        with zamek:
            with plik.open('a', encoding='utf-8') as f:
                f.write(json.dumps(gra, ensure_ascii=False) + '\n')
            film = folder / 'powtorki' / f'{gra["powtorka"]}.mp4'
            if gra['wynik'] in ('zgon', 'limit') and filmy < MAKS_FILMOW and film.is_file():
                shutil.copyfile(film, wyniki / 'filmy' / f'{args.wersja}_{seed}_{gra["wynik"]}.mp4')
                filmy += 1
            tiki = gra['tiki'] if gra['tiki'] is not None else '-'
            print(f'{seed} {gra["wynik"]:7} {tiki:>5} {gra["czas_s"]:6.1f} s'
                  + (f'  {gra["opis"]}' if gra.get('opis') else ''), flush=True)
        return gra

    with ThreadPoolExecutor(rownolegle) as pula:
        gry = list(pula.map(jedna, lista))
    czas = round(time.monotonic() - start, 1)
    zapisz_json(wyniki / f'przebieg_{args.wersja}.json', {
        'seedy': lista, 'rownolegle': rownolegle, 'procesory': os.cpu_count(), 'czas_s': czas})
    bledy = sum(g['wynik'] == 'blad' for g in gry)
    print(f'{args.wersja}: {len(gry)} gier w {czas} s, błędów {bledy}', flush=True)
    return 1 if bledy else 0


# sprawdz_wszystko.py

def sprawdz(args: argparse.Namespace) -> int:
    folder = Path(args.folder).resolve()
    wyniki = Path(args.wyniki).resolve()
    wyniki.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    opis = None
    with (wyniki / 'sprawdz_wszystko.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([sys.executable, 'sprawdz_wszystko.py'], cwd=folder, env=srodowisko(),
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            kod = proc.wait(timeout=LIMIT_SPRAWDZ_S)
        except subprocess.TimeoutExpired:
            zabij(proc)
            proc.wait()
            kod, opis = None, f'przerwany po {LIMIT_SPRAWDZ_S // 60} min'
    czas = round(time.monotonic() - start, 1)
    zapisz_json(wyniki / 'sprawdz.json', {'kod': kod, 'czas_s': czas, 'opis': opis, 'procesory': os.cpu_count()})
    print((wyniki / 'sprawdz_wszystko.log').read_text(encoding='utf-8', errors='replace'), flush=True)
    print(f'sprawdz_wszystko.py: kod {kod} po {czas} s', flush=True)
    return 0 if kod == 0 else 1


# Podsumowanie

def wczytaj(sciezka: Path) -> list[dict]:
    if not sciezka.is_file():
        return []
    return [json.loads(linia) for linia in sciezka.read_text(encoding='utf-8').splitlines() if linia.strip()]


def p_znakow(a: int, b: int) -> float:
    """Dokładny test znaków (dwustronny): jak łatwo o podział a:b przy rzutach monetą."""
    n, k = a + b, min(a, b)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def liczba(x: float, miejsc: int = 1) -> str:
    return f'{x:.{miejsc}f}'.replace('.', ',')


def czas(sekundy: float | None) -> str:
    if sekundy is None:
        return '?'
    m, s = divmod(round(sekundy), 60)
    return f'{m} min {s} s' if m else f'{s} s'


def tiki(t: float | None) -> str:
    if t is None:
        return '-'
    return f'{t:g} ({liczba(t / TIKI_NA_SEKUNDE)} s)'


def statystyka(gry: list[dict]) -> dict:
    wyjscia = [g['tiki'] for g in gry if g['wynik'] == 'wyjscie']
    st = {k: sum(g['wynik'] == k for g in gry) for k in ('wyjscie', 'zgon', 'limit', 'blad')}
    st['gier'] = len(gry)
    st['mediana'] = statistics.median(wyjscia) if wyjscia else None
    return st


def opis_gry(g: dict | None) -> str:
    if g is None:
        return 'brak'
    if g['wynik'] == 'blad':
        return 'błąd'
    nazwa = {'wyjscie': 'wyjście', 'zgon': 'zgon', 'limit': 'limit czasu'}[g['wynik']]
    return f'{nazwa}, {g["tiki"]}'


def werdykt(master: dict, pr: dict) -> tuple[str, list[str], bool]:
    """Zwraca werdykt, linie wyjaśnienia i to, czy pull request coś psuje."""
    wspolne = sorted(set(master) & set(pr))
    linie = []
    bledy = sum(pr[s]['wynik'] == 'blad' for s in pr)
    if bledy:
        return f'Błąd: {bledy} gier z tego pull requestu nie skończyło się wynikiem', linie, True
    lepiej = sum(pr[s]['wynik'] == 'wyjscie' and master[s]['wynik'] != 'wyjscie' for s in wspolne)
    gorzej = sum(master[s]['wynik'] == 'wyjscie' and pr[s]['wynik'] != 'wyjscie' for s in wspolne)
    p_wyj = p_znakow(lepiej, gorzej)
    oba = [s for s in wspolne if pr[s]['wynik'] == master[s]['wynik'] == 'wyjscie']
    szybciej = sum(pr[s]['tiki'] < master[s]['tiki'] for s in oba)
    wolniej = sum(pr[s]['tiki'] > master[s]['tiki'] for s in oba)
    p_czas = p_znakow(szybciej, wolniej)
    rozne = [s for s in wspolne if (pr[s]['wynik'], pr[s]['tiki']) != (master[s]['wynik'], master[s]['tiki'])]

    if lepiej or gorzej:
        pewnosc = 'raczej nie przypadek' if p_wyj < 0.05 else 'to może być przypadek'
        linie.append(f'Wyjścia: ten pull request wychodzi tam, gdzie master nie, na {lepiej} seedach, '
                     f'a master tam, gdzie on nie, na {gorzej} ({pewnosc}: p = {liczba(p_wyj, 3)} w teście znaków).')
    else:
        linie.append('Wyjścia: w obu wersjach wyjściem kończą się te same seedy.')
    if oba and (szybciej or wolniej):
        roznice = [pr[s]['tiki'] - master[s]['tiki'] for s in oba]
        pewnosc = 'raczej nie przypadek' if p_czas < 0.05 else 'to może być przypadek'
        linie.append(f'Czas na {len(oba)} seedach z wyjściem w obu wersjach: szybciej na {szybciej}, wolniej na {wolniej}, '
                     f'tak samo na {len(oba) - szybciej - wolniej}; mediana różnicy {statistics.median(roznice):+g} tików '
                     f'({pewnosc}: p = {liczba(p_czas, 3)}).')

    if not rozne:
        return f'Bez zmian: na wszystkich {len(wspolne)} seedach ten sam wynik i ta sama liczba tików co master', linie, False
    if gorzej > lepiej and p_wyj < 0.05:
        return f'Gorzej: {gorzej - lepiej} wyjść mniej niż master na {len(wspolne)} seedach', linie, True
    if lepiej > gorzej and p_wyj < 0.05:
        return f'Lepiej: {lepiej - gorzej} wyjść więcej niż master na {len(wspolne)} seedach', linie, False
    if p_czas < 0.05 and (szybciej or wolniej):
        kierunek = 'Szybciej' if szybciej > wolniej else 'Wolniej'
        wyjscia = 'przy tych samych wyjściach' if not (lepiej or gorzej) else 'przy liczbie wyjść bez pewnej różnicy'
        return f'{kierunek} niż master {wyjscia}', linie, False
    return f'Bez pewnej różnicy na {len(wspolne)} seedach', linie, False


def podsumuj(args: argparse.Namespace) -> int:
    wyniki = Path(args.wyniki)
    gry = {w: wczytaj(wyniki / f'{w}.jsonl') for w in WERSJE}
    po_seedzie = {w: {g['seed']: g for g in gry[w]} for w in WERSJE}
    st = {w: statystyka(gry[w]) for w in WERSJE}
    przebieg = {w: czytaj_json(wyniki / f'przebieg_{w}.json') for w in WERSJE}
    lista = next((p['seedy'] for p in przebieg.values() if p), [])
    spr = czytaj_json(wyniki / 'sprawdz.json')
    log = wyniki / 'sprawdz_wszystko.log'
    log_tekst = log.read_text(encoding='utf-8', errors='replace') if log.is_file() else ''
    sprawdz_ok = bool(spr) and spr['kod'] == 0
    zmiany = []
    if args.zmiany and Path(args.zmiany).is_file():
        zmiany = [z.strip() for z in Path(args.zmiany).read_text(encoding='utf-8').splitlines() if z.strip()]

    out = [f'## Sprawdzenie bota: pull request{f" #{args.numer}" if args.numer else ""} i master\n']
    if gry['pr'] and gry['master']:
        tekst, linie, psuje = werdykt(po_seedzie['master'], po_seedzie['pr'])
        if st['master']['blad']:
            tekst += f'; uwaga: {st["master"]["blad"]} gier master też nie skończyło się wynikiem'
            psuje = True
    else:
        tekst, linie, psuje = 'Brak wyników gier, zobacz log zadań z grami', [], True
    if not sprawdz_ok:
        tekst += '; sprawdz_wszystko.py nie przeszedł'
    out.append(f'**{tekst}.**\n')
    out.append('| Wersja | Gier | Wyjścia | Zgony | Limity czasu | Błędy | Mediana tików wyjść |')
    out.append('|---|---:|---:|---:|---:|---:|---:|')
    for w in WERSJE:
        s = st[w]
        sha = getattr(args, f'{w}_sha')
        nazwa = NAZWY[w] + (f' `{sha[:7]}`' if sha else '')
        out.append(f'| {nazwa} | {s["gier"]} | {s["wyjscie"]} | {s["zgon"]} | {s["limit"]} | {s["blad"]} | {tiki(s["mediana"])} |')
    out.append('')
    out.extend(f'- {linia}' for linia in linie)
    if linie:
        out.append('')

    inne = [s for s in lista if (po_seedzie['pr'].get(s) or {}).get('wynik') != (po_seedzie['master'].get(s) or {}).get('wynik')]
    if inne:
        out.append('Seedy z innym wynikiem (wynik, tiki):\n')
        out.append('| Seed | master | ten pull request |')
        out.append('|---:|---|---|')
        for s in inne[:20]:
            out.append(f'| {s} | {opis_gry(po_seedzie["master"].get(s))} | {opis_gry(po_seedzie["pr"].get(s))} |')
        if len(inne) > 20:
            out.append(f'| … | i {len(inne) - 20} kolejnych | |')
        out.append('')
    bledy = [(w, g) for w in WERSJE for g in gry[w] if g['wynik'] == 'blad']
    out.extend(f'- Błąd ({NAZWY[w]}, seed {g["seed"]}): {g.get("opis", "")}' for w, g in bledy[:5])
    if bledy:
        out.append('')

    out.append('### sprawdz_wszystko.py\n')
    if spr is None:
        out.append('Brak wyniku: nie uruchomił się albo jego zadanie przerwano.')
    elif sprawdz_ok:
        out.append(f'Przeszedł ({czas(spr["czas_s"])}).')
    else:
        powod = spr.get('opis') or f'kod wyjścia {spr["kod"]}'
        out.append(f'**Nie przeszedł** ({powod}, po {czas(spr["czas_s"])}). Koniec logu: `{koncowka(log_tekst, 600)}`')
    wazne = [linia.strip() for linia in log_tekst.splitlines()
             if linia.startswith(('defend_the_center celujacy', 'defend_the_center losowy', 'MAP01: wyjścia', 'Mediana ukończonych'))]
    out.extend(f'- {linia}' for linia in wazne)
    out.append('')

    out.append('### Jak to liczono\n')
    if lista:
        out.append(f'- Seedy: {len(lista)} pierwszych od {PIERWSZY_SEED}, które bot.py przyjmuje ({lista[0]}-{lista[-1]}), '
                   'te same przy każdym pull requeście. Każda gra to osobne `python bot.py SEED`, jak w CONTRIBUTING.md.')
    czasy = []
    for w in WERSJE:
        if przebieg[w] and gry[w]:
            sredni = statistics.mean(g['czas_s'] for g in gry[w])
            czasy.append(f'{NAZWY[w]} {czas(przebieg[w]["czas_s"])} (gra średnio {liczba(sredni)} s, '
                         f'po {przebieg[w]["rownolegle"]} naraz na {przebieg[w]["procesory"]} procesorach)')
    if spr:
        czasy.append(f'sprawdz_wszystko.py {czas(spr["czas_s"])}')
    if czasy:
        out.append(f'- Każda część na osobnej maszynie GitHuba z Windowsem: {"; ".join(czasy)}.')
    out.append('- Ten sam seed i ten sam kod dają tę samą grę co do tiku, więc każda różnica w tabeli wynika ze zmiany w kodzie.')
    out.append('- Pełne wyniki, log sprawdz_wszystko.py i filmy z kilku przegranych gier: artefakty `wyniki-*` na dole strony tego uruchomienia.')
    if zmiany:
        reszta = f' i {len(zmiany) - 15} innych' if len(zmiany) > 15 else ''
        out.append(f'- Zmienione pliki: {", ".join(f"`{z}`" for z in zmiany[:15])}{reszta}.')
    pliki_sprawdzenia = [z for z in zmiany if z.startswith('.github/') and not z.startswith('.github/ISSUE_TEMPLATE/')]
    if pliki_sprawdzenia:
        out.append('')
        out.append(f'> **Uwaga:** ten pull request zmienia pliki samego sprawdzenia ({", ".join(f"`{z}`" for z in pliki_sprawdzenia)}). '
                   'Liczby wyżej policzył kod z tego pull requestu, więc przeczytaj te zmiany, zanim im uwierzysz.')
    if 'requirements.txt' in zmiany:
        out.append('')
        out.append('> Ten pull request zmienia `requirements.txt`: obie wersje grały na paczkach z tego pull requestu.')

    tekst_md = '\n'.join(out) + '\n'
    print(tekst_md)
    # Czerwony znak: coś się psuje. Wolniejszy bot przy tych samych wyjściach dostaje
    # tylko ostrzeżenie, bo zmiana może kupować niezawodność czasem, a na tych seedach
    # master wychodzi prawie zawsze, więc zysku w wyjściach nie widać.
    nie_uda = psuje or not sprawdz_ok
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(tekst_md)
        rodzaj = 'warning' if nie_uda or tekst.startswith('Wolniej') else 'notice'
        print(f'::{rodzaj} title=Sprawdzenie bota::{tekst}.')
    return 1 if nie_uda else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='polecenie', required=True)
    sub.add_parser('seedy', help='wypisz seedy sprawdzenia')
    p = sub.add_parser('graj', help='zagraj jedną wersją bota na seedach sprawdzenia')
    p.add_argument('--wersja', choices=WERSJE, required=True)
    p.add_argument('--folder', required=True, help='folder z kodem tej wersji')
    p.add_argument('--wyniki', required=True)
    p.add_argument('--rownolegle', type=int, help='ile gier naraz (domyślnie połowa liczby procesorów)')
    p = sub.add_parser('sprawdz', help='uruchom sprawdz_wszystko.py')
    p.add_argument('--folder', required=True)
    p.add_argument('--wyniki', required=True)
    p = sub.add_parser('podsumuj', help='tabela wyników po polsku')
    p.add_argument('--wyniki', required=True)
    p.add_argument('--numer', help='numer pull requestu')
    p.add_argument('--pr-sha', dest='pr_sha')
    p.add_argument('--master-sha', dest='master_sha')
    p.add_argument('--zmiany', help='plik z listą zmienionych plików, po jednym w linii')
    args = parser.parse_args()
    if args.polecenie == 'seedy':
        print(' '.join(map(str, seedy())))
        return 0
    return {'graj': graj, 'sprawdz': sprawdz, 'podsumuj': podsumuj}[args.polecenie](args)


if __name__ == '__main__':
    sys.exit(main())
