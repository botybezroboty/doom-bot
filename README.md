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
.\.venv\Scripts\python.exe bot.py 1 5
```

`bot.py` uruchamia bota na MAP01 dla podanych seedów. Każda próba ma w `powtorki/` powtórkę LMP, wideo MP4 i dziennik JSONL. Bot steruje się po bieżącej pozycji i kierunku, korzystając z punktów znanej mapy. Ustawia poziom trudności 3; poziom historycznych gier ręcznych jest nieznany. Wyniki i ograniczenia znajdują się w `wyniki.md`. Seedy powodujące obcięcie wartości silnika są odrzucane.

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

Każda nowa gra ma obok powtórki `.lmp` plik `.mp4` (obraz 35 klatek/s,
bez dźwięku) i dziennik `.jsonl`. Każdy wiersz `tik` opisuje stan przed
wykonaniem akcji: czas, życie, amunicję wybranej broni, liczbę zabójstw,
widoczne etykiety z pozycją i rozmiarem oraz akcję `[lewo, prawo, strzał]`.
`pozostale_tiki_akcji` obejmuje bieżący tik. Obraz w MP4 pokazuje te same
klatki; wiersz `koniec` zapisuje stan końcowy. Nagrania i dzienniki nie są
przechowywane w Git. Wideo używa kodeka H.264 i formatu kolorów yuv420p.
Na Windows skrypt na czas każdej rozgrywki zwiększa dokładność zegara do 1 ms,
co skraca oczekiwanie ViZDoom; po zakończeniu gry przywraca poprzednie żądanie
dokładności. Wyniki pomiaru i porównania przebiegów znajdują się w `wyniki.md`.

```powershell
.\.venv\Scripts\python.exe defend_the_center.py --trials 100
```

Porównanie aktualnego bota z dawną serią 100 wyników z `porownanie.csv`
można uruchomić poleceniem `.\.venv\Scripts\python.exe porownaj_demony.py`.
Skrypt wymaga zachowanych dawnych powtórek i zapisuje
wyniki par w `porownanie_demony.csv`.

Bot obraca się, aż środek ekranu znajdzie się w obrysie wybranego przeciwnika,
i wtedy strzela.
`porownaj_amunicje.py` porównuje go na 100 tych samych seedach z serią
`porownanie_demony.csv`; wymaga jej powtórek i dzienników, a wyniki zapisuje
w `porownanie_amunicji.csv`. Zużycie poza celem jest oszacowaniem z dziennika,
nie pomiarem rzeczywistych chybień.
`porownaj_trzy.py` porównuje wcześniejsze dwie serie z aktualną na tych samych
100 seedach, sprawdza zachowane dzienniki i powtórki oraz zapisuje dane do
`porownanie_trzech.csv`.

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
