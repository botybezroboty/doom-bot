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
- plików z folderu `powtorki`, filmów, folderu `.venv` i innych dużych plików,
- kilku niezwiązanych zmian naraz.

Zasady pojedynku są w [cel.md](cel.md): bot jest zwykłym skryptem, może znać poziom na pamięć, a w trakcie gry korzysta z tego, co widać na ekranie, i z własnej pozycji. Trzymaj się ich albo napisz wprost, którą zmieniasz i dlaczego.

## Zanim wyślesz zmianę w bocie

1. Zrób fork i osobną gałąź. Jedna zmiana na jeden pull request.
2. Do strojenia używaj dowolnych seedów poniżej 7000. Zakres 7001-7100 zostaw na pomiar na końcu.
3. Sprawdź, że wszystko dalej działa:

   ```powershell
   .\.venv\Scripts\python.exe sprawdz_wszystko.py
   ```

   To polecenie nadpisuje dwa pliki z wynikami. Przywróć je, żeby nie trafiły do pull requestu:

   ```powershell
   git restore dowod_center.csv dowod_map01.csv
   ```

4. Zmierz swoją wersję na seedach 7001-7100:

   ```powershell
   7001..7100 | ForEach-Object { .\.venv\Scripts\python.exe bot.py $_ 2>$null } | Tee-Object wynik-moj.txt
   ```

   Około połowy numerów bot odrzuca, bo na Windowsie biblioteka obcina zbyt duże seedy silnika. Pętla je pomija, więc zostaje około 50 gier i kilka minut czekania. Każda linia to jedna gra: seed, wynik (`wyjscie`, `zgon` albo `limit`) i liczba tików. 35 tików to sekunda gry.

5. Zmierz tak samo obecną wersję:

   ```powershell
   git switch master
   7001..7100 | ForEach-Object { .\.venv\Scripts\python.exe bot.py $_ 2>$null } | Tee-Object wynik-master.txt
   git switch -
   ```

6. Policz wyjścia w obu plikach:

   ```powershell
   (Select-String -Path wynik-moj.txt -Pattern " wyjscie ").Count
   (Select-String -Path wynik-master.txt -Pattern " wyjscie ").Count
   ```

7. Obejrzyj film przynajmniej z jednej gry po zmianie (folder `powtorki`). Sam wynik w tabeli potrafi zmylić, w filmie o bocie zdarzyło się to kilka razy.

Do zmian w README i instrukcjach kroki 2-7 nie są potrzebne.

## Co napisać w pull requeście

- co zmieniasz i dlaczego, w dwóch albo trzech zdaniach,
- wyniki z seedów 7001-7100 dla obecnej wersji i dla Twojej: ile gier, ile wyjść, zgonów i limitów czasu,
- którą zasadę z `cel.md` zmieniasz, jeśli którąś.

Formularz pull requestu ma na to gotowe miejsca.

Możesz pracować z agentem AI, tak powstał cały ten bot. Wynik musisz jednak uruchomić i zmierzyć sam: raport agenta to za mało.

## Jak oceniamy

Liczy się wynik na seedach, których nie było przy strojeniu: najpierw liczba wyjść, potem czas. Zmianę uruchamiamy u siebie na własnych seedach, więc wynik w opisie musi dać się powtórzyć.

Nie obiecujemy terminu odpowiedzi. Poprawki, które wejdą, mogą pojawić się w kolejnym filmie na kanale razem z nazwą konta autora. Jeśli tego nie chcesz, napisz to w pull requeście.

## Licencja i język

Wysyłając pull request, zgadzasz się, że Twoja zmiana jest na licencji MIT, tak jak reszta repozytorium ([LICENSE](LICENSE)).

Pisz po polsku albo po angielsku. Opisy commitów krótkie i po polsku, jak w historii projektu.
