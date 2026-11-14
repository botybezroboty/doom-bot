# Cel i zasady pojedynku

Bot ma przejść MAP01 szybciej od człowieka.

- Gramy w dołączony do ViZDoom Freedoom 2, MAP01, od nowej gry, na tym samym poziomie trudności i tej samej wersji gry oraz konfiguracji mapy. Przed właściwym pojedynkiem trzeba zapisać te wersje, poziom i seed każdej próby.
- Czas obu stron to liczba tików symulacji od początku próby do wyjścia; 35 tików to sekunda czasu gry. Porównujemy całkowite liczby tików, nie czas zegarowy.
- Liczy się tylko ukończenie przez wyjście bez śmierci. Przerwanie, błąd i limit czasu nie są ukończeniem. Każda próba ma powtórkę w `powtorki/`.
- Wynik każdej strony to jej najlepsze poprawne przejście; bot wygrywa, gdy ma mniej tików niż najlepszy wynik człowieka. Należy podawać także liczbę wszystkich prób i ukończeń.
- Bot jest regułowy, bez ML i modeli AI w trakcie gry; może korzystać z informacji udostępnianych przez ViZDoom.

Dotychczasowy rekord człowieka i ograniczenia jego weryfikacji są w `wyniki.md`.
