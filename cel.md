# Cel i zasady pojedynku

Bot ma przejść MAP01 szybciej od człowieka.

- Gramy w dołączony do ViZDoom Freedoom 2, MAP01, od nowej gry, na tym samym poziomie trudności i tej samej wersji gry oraz konfiguracji mapy. Przed właściwym pojedynkiem trzeba zapisać te wersje, poziom i seed każdej próby.
- Czas obu stron to liczba tików symulacji od początku próby do wyjścia; 35 tików to sekunda czasu gry. Porównujemy całkowite liczby tików, nie czas zegarowy.
- Liczy się tylko ukończenie przez wyjście bez śmierci. Przerwanie, błąd i limit czasu nie są ukończeniem. Każda próba ma powtórkę w `powtorki/`.
- Wynik każdej strony to jej najlepsze poprawne przejście; bot wygrywa, gdy ma mniej tików niż najlepszy wynik człowieka. Należy podawać także liczbę wszystkich prób i ukończeń.
- Bot jest zwykłym skryptem regułowym, bez uczenia maszynowego i modeli AI podczas gry.
- Może z góry znać całą mapę oraz początkową liczbę, rodzaje i rozmieszczenie potworów, jak gracz znający poziom na pamięć.
- Podczas gry może korzystać z obrazu ekranu oraz własnej pozycji i kierunku patrzenia. Nie może odczytywać bieżących pozycji niewidocznych potworów ani innych ukrytych informacji o stanie świata.
- Decyzje muszą wynikać z bieżącej obserwacji i reguł; odtwarzanie nagranych ruchów jest zabronione.
- Ten sam poziom trudności co w grze człowieka; bez kodów, wyłączania potworów i innych ułatwień. Historyczny poziom trudności człowieka jest nieznany, co ogranicza porównanie.

## Kolejność prac

1. Opracować prostą nawigację po znanej mapie, sterowaną bieżącą pozycją i kierunkiem.
2. Uruchamiać próby na różnych seedach, zapisując powtórki, wideo i wyniki; diagnozować przeszkody i poprawiać reguły.
3. Doprowadzić bota do wyjścia bez śmierci, a następnie poprawiać czas poniżej 3027 tików i sprawdzić wynik na kolejnych seedach.

Dotychczasowy rekord człowieka i ograniczenia jego weryfikacji są w `wyniki.md`.
