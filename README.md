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
a każda próba zapisuje powtórkę do `powtorki/`.

```powershell
.\.venv\Scripts\python.exe defend_the_center.py --trials 100
```

Tryb ręczny:

```powershell
.\.venv\Scripts\python.exe graj_recznie.py
```

W trybie ręcznym sterujesz w oknie gry: **WASD** — ruch, **mysz** — obrót,
**lewy przycisk myszy** — strzał, **E** lub **spacja** — użyj, **Shift** — bieg.
Kursor jest ukryty tylko w oknie gry; kursor pulpitu pozostaje normalny. Czas od
startu MAP01 do wyjścia dopisywany jest do `wyniki.md`; każda próba ma powtórkę
w `powtorki/`. Próba zakończona śmiercią nie jest liczona jako wynik.
