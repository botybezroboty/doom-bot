# Bot do Freedooma

Prosty bot sterowany regułami, bez uczenia maszynowego. Gra w Freedoom 2 przez ViZDoom.

## Uruchomienie

Wymagany Python 3.10+ x64 na Windows.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bot.py
```

Skrypt uruchamia MAP01 w oknie i zapisuje powtórkę w `powtorki/`.
