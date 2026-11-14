# Bot do Freedooma

Prosty bot sterowany regułami, bez uczenia maszynowego. Gra w Freedoom 2 przez ViZDoom.

## Zasady projektu

Szczegółowe, trwałe zasady dla kolejnych czatów znajdują się w [AGENTS.md](AGENTS.md).
W skrócie: używamy zwykłych skryptów Python bez ML/AI w trakcie gry, ViZDoom
i dołączonego Freedooma, pracujemy w tym repozytorium i `.venv`, zapisujemy każdą
rozgrywkę w `powtorki/`, a po każdym działającym kroku robimy commit po polsku.

## Uruchomienie

Wymagany Python 3.10+ x64 na Windows.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bot.py
```

`bot.py` uruchamia prostego bota na MAP01 i zapisuje powtórkę w `powtorki/`.

## Scenariusz defend_the_center

`defend_the_center.py` porównuje bota celującego po ekranowych etykietach
obiektów z botem losowym. Oba grają bez okna, dostają ten sam zestaw seedów,
a każda próba zapisuje powtórkę do `powtorki/`. Skrypt dobiera seedy tak, aby
uniknąć ograniczenia wartości seeda silnika na Windows, sprawdza seed zapisany
w każdej powtórce i zapisuje szczegóły wraz z odciskami obrazów w `porownanie.csv`.
Skrypt wymusza sterownik SDL `dummy` i używa osobnej ukrytej instancji gry
dla serii każdego bota. Sprawdza istnienie powtórek i seedy w nagłówkach,
ale nie odtwarza ich ani nie weryfikuje w ten sposób wyników. Ponowne
uruchomienie nadpisuje `porownanie.csv`; powtórki nie są zapisane w Git.
`requirements.txt` nie przypina wersji zależności, więc środowisko może się różnić.

Każda nowa gra ma obok powtórki `.lmp` plik `.avi` (obraz 35 klatek/s,
bez dźwięku) i dziennik `.jsonl`. Każdy wiersz `tik` opisuje stan przed
wykonaniem akcji: czas, życie, amunicję wybranej broni, liczbę zabójstw,
widoczne etykiety z pozycją i rozmiarem oraz akcję `[lewo, prawo, strzał]`.
`pozostale_tiki_akcji` obejmuje bieżący tik. Obraz w AVI pokazuje te same
klatki; wiersz `koniec` zapisuje stan końcowy. Nagrania i dzienniki nie są
przechowywane w Git. AVI zawiera bezstratne klatki PNG; potrzebny jest
odtwarzacz obsługujący ten kodek, np. VLC.

```powershell
.\.venv\Scripts\python.exe defend_the_center.py --trials 100
```

Tryb ręczny:

```powershell
.\.venv\Scripts\python.exe graj_recznie.py
```

W trybie ręcznym sterujesz w oknie gry: **WASD** — ruch, **mysz** — obrót,
**lewy przycisk myszy** — strzał, **E** lub **spacja** — użyj, **Shift** — bieg.
Kursor jest ukryty tylko w oknie gry; kursor pulpitu pozostaje normalny. Czas
próby jest liczony w tikach symulacji (35 tików na sekundę czasu gry), zgodnie
z zasadami w `cel.md`. Wynik bez śmierci jest dopisywany do `wyniki.md`; każda
próba ma powtórkę w `powtorki/`. Obecny kod rozpoznaje koniec epizodu bez
śmierci, nie ma osobnego potwierdzenia wyjścia.
