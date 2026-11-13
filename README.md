# Bot do Freedooma

Prosty bot sterowany regułami, bez uczenia maszynowego. Gra w Freedoom 2 przez ViZDoom.

## Uruchomienie

Wymagany Python 3.10+ x64 na Windows.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bot.py
```

`bot.py` uruchamia prostego bota na MAP01 i zapisuje powtórkę w `powtorki/`.

Tryb ręczny:

```powershell
.\.venv\Scripts\python.exe graj_recznie.py
```

W trybie ręcznym sterujesz w oknie gry: **WASD** — ruch, **mysz** — obrót,
**lewy przycisk myszy** — strzał, **E** lub **spacja** — użyj, **Shift** — bieg.
Kursor jest ukryty tylko w oknie gry; kursor pulpitu pozostaje normalny. Czas od
startu MAP01 do wyjścia dopisywany jest do `wyniki.md`; każda próba ma powtórkę
w `powtorki/`. Próba zakończona śmiercią nie jest liczona jako wynik.
