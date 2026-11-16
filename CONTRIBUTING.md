# Jak pomóc przy bocie

Dzięki, że chcesz pomóc. Ten plik mówi, gdzie co zgłaszać i co ma być w pull requeście, żeby dało się go szybko ocenić.

## Gdzie z czym

| Masz | Idź tu |
|---|---|
| pytanie albo coś nie działa | [Discord](https://discord.gg/6QCNXAGntW), kanał `pomoc` |
| własnego bota, także do innej gry | Discord, kanał `wasze-boty` |
| pomysł na bota | Discord, kanał `pomysły-na-boty` |
| błąd w tym repozytorium: skrypt się wywala albo README mówi nieprawdę | issue |
| poprawkę tego bota albo instrukcji | pull request |

## Co przyjmujemy

- poprawki bota: mniej przegranych gier, krótszy czas, kolejne poziomy,
- poprawki błędów w skryptach,
- poprawki README i pozostałych instrukcji.

Jako pull requestu nie przyjmujemy:

- innego bota albo bota przepisanego od zera. Zrób go we własnym forku i pokaż na Discordzie,
- plików z folderu `replays`, filmów, folderu `.venv` i innych dużych plików,
- kilku niezwiązanych zmian naraz.

Zasady pojedynku są w [goal.md](goal.md): bot jest zwykłym skryptem, może znać poziom na pamięć, a w trakcie gry korzysta z tego, co widać na ekranie, i z własnej pozycji. Trzymaj się ich albo napisz wprost, którą zmieniasz i dlaczego.

## Zanim wyślesz zmianę w bocie

1. Zrób fork i osobną gałąź. Jedna zmiana na jeden pull request.
2. Do strojenia używaj dowolnych seedów poniżej 7000. Zakres 7001-7100 zostaw na pomiar na końcu. Seedów od 8001 wzwyż nie używaj wcale: na nich gra automatyczne sprawdzenie (opis niżej).
3. Sprawdź, że wszystko dalej działa:

   ```powershell
   .\.venv\Scripts\python.exe check_all.py
   ```

   To polecenie nadpisuje dwa pliki z wynikami. Przywróć je, żeby nie trafiły do pull requestu:

   ```powershell
   git restore proof_center.csv proof_map01.csv
   ```

4. Zmierz swoją wersję na seedach 7001-7100:

   ```powershell
   7001..7100 | ForEach-Object { .\.venv\Scripts\python.exe bot.py $_ 2>$null } | Tee-Object result-mine.txt
   ```

   Około połowy numerów bot odrzuca, bo na Windowsie biblioteka obcina zbyt duże seedy silnika. Pętla je pomija, więc zostaje około 50 gier i kilka minut czekania. Każda linia to jedna gra: seed, wynik (`exit`, `death` albo `timeout`) i liczba tików. 35 tików to sekunda gry.

5. Zmierz tak samo obecną wersję:

   ```powershell
   git switch master
   7001..7100 | ForEach-Object { .\.venv\Scripts\python.exe bot.py $_ 2>$null } | Tee-Object result-master.txt
   git switch -
   ```

6. Policz wyjścia w obu plikach:

   ```powershell
   (Select-String -Path result-mine.txt -Pattern " exit ").Count
   (Select-String -Path result-master.txt -Pattern " exit ").Count
   ```

7. Obejrzyj film przynajmniej z jednej gry po zmianie (folder `replays`). Sam wynik w tabeli potrafi zmylić, w filmie o bocie zdarzyło się to kilka razy.

Do zmian w README i instrukcjach kroki 2-7 nie są potrzebne.

## Co napisać w pull requeście

- co zmieniasz i dlaczego, w dwóch albo trzech zdaniach,
- wyniki z seedów 7001-7100 dla obecnej wersji i dla Twojej: ile gier, ile wyjść, zgonów i limitów czasu,
- którą zasadę z `goal.md` zmieniasz, jeśli którąś.

Formularz pull requestu ma na to gotowe miejsca.

Możesz pracować z agentem AI, tak powstał cały ten bot. Wynik musisz jednak uruchomić i zmierzyć sam: raport agenta to za mało.

## Automatyczne sprawdzenie

Każdy pull request, który zmienia coś więcej niż instrukcje, sprawdza GitHub Actions na Windowsie. Trwa to około 10 minut (dłużej, gdy bot często nie zdąży przed limitem czasu), a trzy osobne maszyny robią naraz trzy rzeczy:

- bot z Twojego pull requestu gra na 40 stałych seedach,
- bot z `master` gra na tych samych seedach,
- `check_all.py` sprawdza Twoją wersję.

Wynik jest w pull requeście w zakładce **Checks**, w **Summary**: liczba gier, wyjść, zgonów i limitów czasu obu wersji, mediana tików, seedy z innym wynikiem i to, czy `check_all.py` przeszedł. Niżej na tej stronie są do pobrania wyniki i filmy z kilku przegranych gier.

Sprawdzenie kończy się błędem, gdy któraś gra się wywali, gdy `check_all.py` nie przejdzie albo gdy Twoja wersja wychodzi z poziomu rzadziej niż `master`, a różnica nie wygląda na przypadek. Wolniejszy bot przy tych samych wyjściach dostaje ostrzeżenie, nie błąd.

Seedy sprawdzenia to 40 pierwszych numerów od 8001, które `bot.py` przyjmuje: od 8001 do 8088. Nie strój na nich bota i nie podawaj na nich wyniku w opisie:

- to inne gry niż Twoje 7001-7100, więc sprawdzenie jest drugą, niezależną próbą,
- lista jest stała, więc wyniki różnych pull requestów da się ze sobą porównać,
- 40 gier wystarczy, żeby zobaczyć zepsutą zmianę, ale nie odróżni poprawki o jedną grę na sto. Do tego służy Twój pomiar na 7001-7100.

Ten sam seed i ten sam kod dają tę samą grę co do tiku, także na maszynach GitHuba. Grę, która w sprawdzeniu skończyła się inaczej niż u Ciebie, powtórzysz poleceniem `.\.venv\Scripts\python.exe bot.py SEED`.

Pliki sprawdzenia (`.github/workflows/pr-check.yml`, `.github/pr_check.py`) zmieniaj tylko osobnym pull requestem. Gdy pull request je zmienia, liczby w podsumowaniu liczy jego własny kod, więc nie traktujemy ich jak niezależnego pomiaru.

## Jak oceniamy

Liczy się wynik na seedach, których nie było przy strojeniu: najpierw liczba wyjść, potem czas. Zmianę uruchamiamy u siebie na własnych seedach, więc wynik w opisie musi dać się powtórzyć.

Nie obiecujemy terminu odpowiedzi. Poprawki, które wejdą, mogą pojawić się w kolejnym filmie na kanale razem z nazwą konta autora. Jeśli tego nie chcesz, napisz to w pull requeście.

## Licencja i język

Wysyłając pull request, zgadzasz się, że Twoja zmiana jest na licencji MIT, tak jak reszta repozytorium ([LICENSE](LICENSE)).

Pisz po polsku albo po angielsku. Opisy commitów krótkie i po polsku, jak w historii projektu.
