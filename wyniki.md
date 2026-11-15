# Wyniki gry ręcznej

## Niezawodność — 80 znanych + 100 odłożonych seedów (15.11.2026)

**Cel pełnej niezawodności nie został osiągnięty:** poprawiona wersja ma 179 wyjść na 180 prób. Na odłożonych seedach pozostał jeden zgon. Wszystkie 179 ukończeń nowej wersji trwało mniej niż 3027 tików; najwolniejsze 2797.

| Zestaw | Wersja | Wyjścia | Zgony | Limit | Mediana tików ukończeń |
|---|---|---:|---:|---:|---:|
| Znane 80 | Przed | 71 | 9 | 0 | 1649 |
| Znane 80 | Po | 80 | 0 | 0 | 1743 |
| Odłożone 100 | Przed | 87 | 13 | 0 | 1715 |
| Odłożone 100 | Po | 99 | 1 | 0 | 1809 |

Mediana obejmuje tylko ukończenia, więc zestawy ukończonych seedów różnią się między wersjami. Nowa mediana jest o 94 tiki większa w obu zestawach, przy znacznie większej liczbie wyjść. ViZDoom 1.3.2, dołączony Freedoom 2 MAP01, trudność 3, limit 3500; konfiguracja i `cel.md` zachowane. Trudność historycznych prób człowieka nadal jest nieznana.

### Diagnoza dawnych dziewięciu zgonów

W dziennikach i klatkach filmów wszystkie dziewięć przypadków poprzedza duża utrata życia przy beczkach w pierwszej sali. Dawna reguła biegła z pełną prędkością do wąskiego, odległego celu i strzelała w pobliżu beczek. Część prób kończyła się bezpośrednio przy wybuchu, pozostałe znacznie później, po dalszej walce z bardzo małą ilością życia. Dziennik nie wskazuje sprawcy każdego trafienia; związek z wybuchami ustalono z przebiegu i obrazu, a nie z osobnego licznika źródła obrażeń.

| Seed | Tiki dużych ubytków życia i wielkość ubytku | Tik zgonu |
|---|---|---:|
| 1010 | 540: 127 HP | 540 |
| 1030 | 519: 55 HP, 541: 86 HP | 541 |
| 1032 | 298: 58 HP, 314: 46 HP | 314 |
| 1041 | 371: 84 HP | 588 |
| 1056 | 529: 84 HP | 1154 |
| 1085 | 298: 68 HP | 1556 |
| 1092 | 404: 86 HP | 617 |
| 1144 | 499: 36 HP, 512: 27 HP | 1804 |
| 1161 | 460: 76 HP | 1461 |

Ubytki liczą różnicę wartości HEALTH, także jej zejście poniżej zera. Pełne pozycje, odległości do początkowych punktów beczek i nazwy nagrań: [diagnoza_niezawodnosc.json](diagnoza_niezawodnosc.json); odtworzenie zestawienia: `diagnozuj_zgony.py`. [Klatki dziewięciu dawnych przypadków](powtorki/diagnoza_zgonow.png) są ułożone w kolejności seedów z powyższej tabeli.

Bot teraz wolniej podchodzi do odległych przeciwników i zatrzymuje się przy bliższych. Widoczne beczki o małym obrysie ostrzeliwuje przed dalszym ruchem; próba ma ograniczony czas, a ponowienie wymaga zmiany pozycji. Po ostrzale i przy widocznej eksplozji czeka, ponieważ podmuch przesuwa kolejne beczki, a wybuch łańcuchowy trwa jeszcze po zniszczeniu pierwszej. Przy braku amunicji podejmuje nawigację. Wszystkie decyzje pochodzą ze skryptu regułowego, bieżącego obrazu/etykiet widocznych obiektów i własnej pozycji; bot nie odczytuje położeń niewidocznych aktorów.

Zachowano trasę, zbieranie przedmiotów, wybór strzelby i obsługę wyjścia. Nowa wersja zdobyła i wybrała strzelbę oraz osiągnęła co najmniej 100 pancerza na wszystkich znanych 80 seedach. Dodatkowa regresja na dawnych 20 seedach z `seedy_nawigacja_etap.json` dała 20 wyjść, 0 zgonów, 0 limitów; mediana 1862, maksimum 2447. Przeszły także cztery istniejące testy celowania.

### Niezależność testu i pozostałe niepowodzenie

Listę 100 nowych, niepowtarzających się seedów zapisano przed zmianami w commicie `12b4033` (`seedy_niezawodnosc_odlozone.json`). Stara wersja to `bf1411a`, zachowana w `bot_przed_niezawodnoscia.py`. Kod poprawki zapisano w `2bf2a83`, sumy kontrolne i środowisko zamrożono w `55c7742` (`zamrozenie_niezawodnosc.json`). Po rozpoczęciu testu odłożonego kod bota nie był zmieniany. Lista 80 znanych i dodatkowe 20 dawnych seedów służyły rozwojowi, więc ich wynik nie jest niezależną oceną.

Na znanych 80 wykorzystano zachowane próby końcowej poprawki; starą wersję rozegrano ponownie. Jej wszystkie wyniki i czasy zgadzają się z dawną tabelą. Na odłożonych 100 obie wersje rozegrano od nowa. Każde zgłoszone wyjście odtworzono i potwierdzono czas, brak śmierci i użycie przełącznika przy końcu. Jak wcześniej, ViZDoom nie dostarcza tu osobnego sygnału wyjścia. Sprawdzono komplet LMP/MP4/JSONL i seed w nagłówku każdej próby.

Pozostały zgon kontrolny: **seed 1226, tik 589**, około (1141, -274), przed dotarciem do pancerza. Życie malało stopniowo pod ostrzałem, bez dużego jednorazowego ubytku charakterystycznego dla dawnych wybuchów. Bot długo pozostawał przed wejściem do sali (m.in. tiki 121–361), tracąc życie ze 100 do 61 przy zerowym pancerzu; w tiku 541 miał już 10 HP. To pozostała słabość postoju podczas walki i ostrzału beczek. Nagranie obejrzano dopiero po zakończeniu serii, wyłącznie do opisu ograniczenia; nie użyto go do poprawiania kodu. [Klatki tiku 400 i 580](powtorki/diagnoza_kontrolna_1226.png), [pełne wideo](powtorki/map01_nowy_1226_20261115_100940_129205.mp4).

Końcowe pary są w [porownanie_niezawodnosc.csv](porownanie_niezawodnosc.csv), a wyniki poszczególnych zestawów w `niezawodnosc_<seria>_<wersja>.csv`. Ta sesja obejmowała **565 nowych rozgrywek: 538 wyjść, 25 zgonów, 2 limity**, wszystkie z kompletem nagrań. Końcowe porównanie to 360 prób; poza nim wykonano 205 prób diagnostycznych i regresyjnych (201 wyjść, 2 zgony, 2 limity). Pełny rejestr: [proby_niezawodnosc_wszystkie.csv](proby_niezawodnosc_wszystkie.csv). Wynik 99/100 nie uprawnia do deklarowania przejścia każdej gry.

## Stała strzelba i odzyskiwanie trasy — 60 + 20 seedów

Strzelba wskazana w filmie leży na podwyższeniu przy (1536, −160). Wejście od
zachodu bezpośrednio na środek jest zbyt wysokie; bot przechodzi teraz po
stopniach od południa, wchodzi na górę i wraca do drzwi. Na seedzie 1002
poprzednia wersja zdobyła pierwszą strzelbę w odległości 864 jednostek od
tego miejsca. Nowa zdobyła ją w tiku 623, 35,5 jednostki od punktu; w
odtwarzanej powtórce bezpośrednio przed tym widoczny jest obiekt strzelby z
mapy w (1536, −160), a następnie gracz ma broń. Wybrał ją w tiku 644.
Nagranie: `map01_nowy_1002_20261114_234112_781372.mp4`.

W starym dzienniku 1084 bot po walce znajdował się na północ od drzwi, a po
przekroczeniu czasu przeznaczonego na apteczkę próbował iść do punktu na
południe od zamkniętej geometrii, krążąc między około (1286, −304) a
(1808, −208). W 1098 próbował przejść ze strony (1744, −685) do punktu za
krawędzią i ścianami, poruszając się w okolicy bez dotarcia do celu. Nowa
trasa wraca do drzwi, jeśli walka przeniosła bota na ich północną stronę,
i prowadzi zachodni odcinek przez przejście przy y≈−850. Oba seedy zakończyły
się wyjściem: odpowiednio 1775 i 1497 tików. Przy diagnozie odkryto też
przypadki powrotu do już zdobytej strzelby i zepchnięcia ze stopni: bot
zapamiętuje dotarcie do niej, a po zepchnięciu podejmuje ograniczone próby
ponownego wejścia.

| Zestaw | Wersja | Wyjścia | Zgony | Limit | Mediana ukończeń | Posiadał strzelbę | Pierwsze zdobycie blisko podwyższenia |
|---|---|---:|---:|---:|---:|---:|---:|
| Wcześniejsze 60 | Przed | 47 | 11 | 2 | 1773 | 51 | 0 |
| Wcześniejsze 60 | Po | 53 | 7 | 0 | 1671 | 55 | 46 |
| Nowe kontrolne 20 | Przed | 15 | 3 | 2 | 1729 | 18 | 0 |
| Nowe kontrolne 20 | Po | 18 | 2 | 0 | 1622 | 20 | 16 |

Mediany obejmują tylko ukończenia; ich zestawy mogą różnić się między
wersjami. Wszystkie ukończenia miały mniej niż 3027 tików. Ostatnia kolumna
jest przybliżeniem: oznacza pierwsze przejście z braku broni do posiadania
w promieniu 40 jednostek od stałej strzelby, a nie identyfikację konkretnego
podniesionego obiektu. Nie obejmuje sytuacji, gdy bot miał strzelbę już
wcześniej. Wiarygodność źródła dla opisanej próby 1002 sprawdzono osobno w
powtórce. Bot może zginąć albo nie zdobyć tej broni w innych okolicznościach.

Trzy wcześniejsze zestawy po 20 pochodzą z `porownanie_strzelba_final.csv`;
część posłużyła do diagnostyki i poprawek. Wstępną serię na seedach 1107–1139
zachowano w `porownanie_nawigacja_etap.csv`; po jej problemie na seedzie
1131 poprawiono ponowne wejście. Ostatnie 20 nowych seedów z pliku
`seedy_nawigacja_kontrolne.json` odłożono przed tą poprawką i nie użyto do
strojenia. W `porownanie_nawigacja.csv` są wszystkie 160 pozycji, czasy,
seedy silnika, nazwy powtórek i przybliżone miejsca zdobycia broni. Każde
nowe zgłoszone wyjście odtworzono i sprawdzono czas, brak zgonu oraz użycie
przełącznika; osobnego sygnału wyjścia ViZDoom tu nie dostarcza. Sprawdzono
komplety LMP/MP4/JSONL i seedy w nagłówkach wszystkich 160 powtórek.
ViZDoom 1.3.2, Freedoom 2 MAP01, trudność 3; trudność dawnych prób ręcznych
pozostaje nieznana.


## Strzelba i przełącznik — porównanie przed i po

Użytkownik wskazał najlepszą próbę z seeda 1002. Jej dziennik nie zapisywał
broni, więc odtworzono LMP: bot ani razu nie posiadał strzelby. Odtworzenie z
ekranowymi etykietami pokazuje widoczną strzelbę. Od wskazania ostatniego
punktu trasy do zakończenia w starej próbie minęło 147 tików; po drodze bot
wielokrotnie mijał punkt i zawracał. W końcowej wersji bot na tym seedzie
podniósł i wybrał strzelbę, a ten odcinek trwał 38 tików. Cała próba trwała
1595 tików wobec wcześniejszych 1525 — zbieranie broni może wydłużyć trasę.
Nagranie po zmianie: `map01_nowy_1002_20261114_225129_916306.mp4`.

Bot próbuje podnieść widoczną strzelbę, gdy jej nie ma, wybiera ją przy
posiadaniu nabojów i rezygnuje z długiego pościgu, jeśli nie robi postępu.
Przy wyjściu ustawia się przed przełącznikiem, podchodzi w jego zasięg i
używa go. Stan broni w próbach obu wersji odczytano z odtwarzanych powtórek;
każde zgłoszone wyjście również sprawdzono przez odtworzenie, brak zgonu i
użycie przy przełączniku. ViZDoom nie daje tu osobnego sygnału wyjścia.

| Seedy (po 20) | Wersja | Wyjścia | Zgony | Limit | Mediana ukończeń | Strzelba zdobyta / wybrana | Mediana ostatniego odcinka |
|---|---|---:|---:|---:|---:|---:|---:|
| Z dowodu | Przed | 16 | 4 | 0 | 1867 | 9 / 9 | 150,5 |
| Z dowodu | Po | 15 | 5 | 0 | 1711 | 16 / 16 | 38 |
| Kolejne | Przed | 18 | 2 | 0 | 1867 | 13 / 13 | 198,5 |
| Kolejne | Po | 18 | 2 | 0 | 1641 | 17 / 17 | 37 |
| Kontrolne | Przed | 16 | 4 | 0 | 1777 | 10 / 10 | 118 |
| Kontrolne | Po | 14 | 4 | 2 | 1886 | 18 / 18 | 38 |

Tiki ostatniego odcinka to czas od pierwszego wybrania ostatniego punktu trasy
do wyjścia; obejmują także ewentualną walkę. Mediany liczą tylko ukończenia,
dlatego różniące się liczby ukończeń ograniczają bezpośrednie porównanie.
Wszystkie ukończenia były poniżej 3027 tików. Strzelba oznacza posiadanie
broni w dowolnej chwili, a wybór — jej aktywowanie w dowolnej chwili, nie
koniecznie oddanie strzału. Na kontrolnych seedach 1084 i 1098 nowa wersja
osiągnęła limit 3500 tików po utknięciu na wcześniejszej części trasy, podczas
gdy stara ukończyła obie próby. Poprawka nie zapewnia więc niezawodności i w
serii kontrolnej pogorszyła odsetek ukończeń.

Seria „z dowodu” zawiera te same 20 seedów co `dowod_map01.csv`. Kolejne 20
wybrano przed próbami; po pierwszym porównaniu użyto seeda 1042 do poprawy
zasięgu wyjścia, więc nie jest to niezależny test końcowej wersji. Następnie
zamrożono dodatkowe 20 nowych seedów kontrolnych, których nie użyto do strojenia.
Poprzednie rezultaty zachowano w `porownanie_strzelba_etap.csv`, końcowe pary
w `porownanie_strzelba_final.csv`, a listy w `seedy_strzelba.json` i
`seedy_strzelba_kontrolne.json`. We wszystkich 120 pozycjach końcowej tabeli
sprawdzono komplet LMP/MP4/JSONL i seed w LMP. Stara wersja dla pierwszych 40
pozycji pochodzi z zachowanych wcześniejszych powtórek; w pozostałych parach
gry uruchomiono ponownie. Środowisko: ViZDoom 1.3.2, Freedoom 2 MAP01,
trudność 3; trudność historycznej gry ręcznej pozostaje nieznana.


## Niezależna seria — jedno polecenie

Po zatwierdzeniu bota w commicie `d3f2f06` uruchomiono
`.\.venv\Scripts\python.exe sprawdz_wszystko.py`. Przed rozpoczęciem
dobrano 20 różnych seedów silnika, których nie było w zachowanych wcześniejszych
powtórkach i tabelach; ich lista oraz wyniki są w `dowod_map01.csv`. Bot nie
był poprawiany na podstawie tej serii. ViZDoom 1.3.2, dołączony Freedoom 2
MAP01, poziom 3, limit 3500 tików.

MAP01: **16 ukończeń, 4 zgony i 0 limitów**. Mediana 16 ukończonych prób:
**1867 tików**, najlepsza 1525; wszystkie ukończenia były poniżej 3027 tików.
Każde z 16 ukończeń osobno odtworzono i sprawdzono liczbę tików, brak śmierci
i użycie przełącznika wyjścia tuż przed końcem. ViZDoom nie dostarcza w tym
skrypcie osobnego sygnału wyjścia; potwierdzenie wynika z tych przesłanek.
Najlepsze wideo: `powtorki/najlepsza_map01_20261114_222152_565722.mp4`;
jego kopię sprawdzono przez SHA-256 z filmem źródłowym. Dane nie dowodzą
równego poziomu trudności z historyczną grą człowieka, bo tam go nie zapisano.

W `defend_the_center` przeszły cztery testy celowania, a na tych samych
20 parach seedów bot celujący zabił średnio **22,65** przeciwnika, losowy
**1,55**. Szczegóły, seedy, czasy i nazwy nagrań są w `dowod_center.csv`.
Wszystkie 60 rozgrywek zapisano jako powtórki, dzienniki i filmy.


## Walka i znajdźki — porównanie 20 seedów

ViZDoom 1.3.2, dołączony Freedoom 2 MAP01, trudność 3, limit 3500 tików.
Ta sama lista 20 różnych seedów silnika dla obu wersji. Stara wersja biegnie
do wyjścia, nowa celuje w widocznych przeciwników, zbiera przedmioty na trasie
i próbuje ominąć miejsce utknięcia. Czas obejmuje całą próbę, także w razie
zgonu. Wszystkie ukończenia nowej wersji trwały mniej niż 3027 tików.

| Wersja | Wyjścia | Zgony | Limit | Tiki wyjść: średnia (zakres) | Tiki zgonów: średnia (zakres) |
|---|---:|---:|---:|---:|---:|
| Stara | 8 | 12 | 0 | 622 (589–697) | 708,2 (440–995) |
| Nowa | 14 | 6 | 0 | 1813 (1501–2101) | 909,2 (328–2006) |

W [porownanie_map01.csv](porownanie_map01.csv) jest każda para wyników, czas,
seed wejściowy i silnika oraz nazwa powtórki. Każda próba ma w `powtorki/`
plik LMP, film MP4 z pełnym HUD i dziennik JSONL. Sprawdzono istnienie
wszystkich 40 kompletów, seed w każdym nagłówku i zgodność dzienników z CSV;
trzy przykładowe ukończenia obu wersji odtworzono i potwierdzono ich czas oraz
brak zgonu. W dziennikach nowej serii odnotowano łącznie 220 zabójstw,
wzrost pancerza w 20 grach, życia w 8 i amunicji wybranej broni w 19.
W czterech grach przyrost życia wyniósł co najmniej 10 punktów. Pozostałe
wzrosty licznika obejmują również drobne bonusy oraz ewentualne zmiany broni,
nie są niezależnym potwierdzeniem każdego rodzaju podniesionego przedmiotu.

Pierwsza wersja reguł walki na tych samych seedach ukończyła 13 gier,
zginęła 2 razy i 5 razy osiągnęła limit; czas ukończeń 1537–3061 tików.
Jej dane zachowano w `porownanie_map01_pierwsze.csv`. Po zauważeniu zacięć
przy apteczce poprawiono reguły i ponownie uruchomiono wszystkie 20 nowych
prób; wyniki starej wersji pozostały te same. Historyczny poziom trudności
gier ręcznych jest nieznany, więc porównanie z rekordem człowieka ma to
zastrzeżenie. Części tych seedów użyto do poprawiania reguł, więc nie jest to niezależna
próba sprawdzająca; wyniki nie gwarantują przeżycia na innych seedach.


## Pierwsze przejścia bota MAP01

ViZDoom 1.3.2, dołączony Freedoom 2, MAP01, poziom 3. Bot bez strzelania
prowadzi nawigację według własnej pozycji i kierunku oraz znanych punktów mapy.
Odtworzenie powtórek potwierdziło wyjście bez zgonu po **601 tikach**:

| Seed wejściowy | Seed silnika | Życie na końcu | Powtórka |
|---:|---:|---:|---|
| 1 | 1791095845 | 74 | `map01_1_20261114_201857_193071.lmp` |
| 5 | 953453411 | 31 | `map01_5_20261114_201900_368210.lmp` |

Obok powtórek są filmy MP4 i dzienniki JSONL. Pierwsze serie i późniejsze
próby obejmują łącznie 36 gier: 8 zakończeń i 28 zgonów; część zakończeń
powtarza ten sam seed silnika, więc nie jest niezależnym wynikiem. Ostatnia
seria miała 5 prób (4 wyjścia, 1 zgon), ale dwa seedy zostały obcięte do
tej samej wartości silnika. Kod teraz odrzuca takie seedy. Poziom trudności
historycznego rekordu człowieka 3027 tików jest nieznany, więc uczciwego
porównania trudności nie potwierdzono. Bot nie jest jeszcze niezawodny.


## Poprawka zatrzymywania celownika

Najgorsza gra poprzedniej wersji: seed wejściowy 210, jeden zabity,
śmierć w tiku 224 i 22 naboje. Powtórzono ją z identycznym wynikiem
i SHA-256 obrazów `9f278010a315bdfbbe9d958e581d91d6db586ac94fa329908091ffc467a068e2`.
Nagranie i dziennik powtórzenia mają nazwę bazową
`center_etykiety_210_20261114_194812_521231` w `powtorki/`.

W 149 z 214 zapisanych tików bot widział rozpoznawanego przeciwnika,
ale jednocześnie nie skręcał i nie strzelał. Na przykład w tiku 200
miał 12 punktów życia i 22 naboje; przeciwnik miał obrys x=164–173,
a środek ekranu to x=160. Błąd polegał na tym, że bot przestawał
skręcać w odległości do 9 pikseli od środka celu, choć warunek strzału
wymagał przecięcia środka ekranu przez jego obrys. Poprawiony bot obraca
się do chwili osiągnięcia tego obrysu. W grze na tym seedzie zabił 26,
przeżył 1149 tików i wyczerpał amunicję w tiku 770. Nowe nagranie:
`center_etykiety_210_20261114_195206_768230.mp4`.

Na tych samych 100 seedach porównano trzy wersje; dwie wcześniejsze serie
pochodzą z zachowanych dzienników i powtórek. Sprawdzono wyniki starych
dzienników, seedy w 300 powtórkach i różne odciski obrazów nowej serii.
Wszystkie gry zakończyły się śmiercią. Szczegóły: `porownanie_trzech.csv`.

| Wynik | Ciągły strzał | Poprzedni obrys | Poprawiony obrys |
|---|---:|---:|---:|
| Średnio zabitych | 10,01 | 11,06 | 22,82 |
| Zakres zabitych | 8–12 | 1–23 | 9–26 |
| Średni czas (tiki) | 663,46 | 711,75 | 1115,85 |
| Średnio zużytych nabojów | 26,00 | 15,78 | 25,73 |
| Średnio zużytych poza obrysem | 17,32 | 4,46 | 0,82 |
| Gry z wyczerpaną amunicją | 100 | 18 | 97 |

Nowa wersja względem poprzedniej zabiła więcej na 96 seedach, tyle samo na
jednym i mniej na trzech (64: 23→21, 158: 22→19, 176: 19→9). Względem
ciągłego strzału wynik wzrósł na 99 seedach, a na jednym był równy.
Pomiar zużycia poza obrysem jest przybliżeniem opisanym poniżej, nie liczbą
potwierdzonych chybień.

## Ograniczenie strzelania w defend_the_center

Porównano serię z `porownanie_demony.csv` z nową na tych samych 100 seedach.
Bot naciska strzał, gdy środek obrazu znajduje się w obrysie wybranego celu;
podczas poszukiwania nie naciska strzału. Seedy obu serii sprawdzono
w nagłówkach 200 powtórek. Dane par są w `porownanie_amunicji.csv`, a każda
nowa gra ma powtórkę, dziennik i wideo w `powtorki/`.

| Wynik | Przed zmianą | Po zmianie |
|---|---:|---:|
| Średnio zabitych | 10,01 | 11,06 |
| Średni czas (tiki) | 663,46 | 711,75 |
| Średnio zużytych nabojów | 26,00 | 15,78 |
| Średnio zużytych poza obrysem celu | 17,32 | 4,46 |
| Gry z wyczerpaną amunicją | 100 | 18 |

Przed zmianą amunicja kończyła się w każdej grze w tiku 371 (10,6 s).
Po zmianie w 18 grach skończyła się między tikami 756 a 1328, średnio
w tiku 938,6. Nowy bot zabił więcej na 48 seedach, tyle samo na 6,
a mniej na 46; zakres wyników wzrósł z 8–12 do 1–23.

Zużycie to suma spadków licznika amunicji między kolejnymi stanami.
„Poza obrysem” oznacza brak rozpoznanej etykiety przeciwnika obejmującej
środek ekranu w stanie bezpośrednio przed spadkiem licznika. To przybliżenie,
nie liczba rzeczywistych chybień: dziennik nie zawiera trafień, a animacja
broni i ruch celu mogą przesuwać moment zużycia względem decyzji o strzale.

## Wydajność defend_the_center

Na Windows, ViZDoom 1.3.2, zmierzono trzy próby bota etykietowego
(seedy 1, 2 i 5), łącznie 1820 tików. Czas obejmuje zapis powtórek,
dzienników i wideo oraz zamknięcie gry, ale nie inicjalizację. Przed zmianą
trwały 28,25 s (64,4 tiku/s); pomiar poszczególnych wywołań wykazał,
że `advance_action` zajęło 27,33 s. Po żądaniu dokładności zegara Windows
1 ms na czas rozgrywki te same próby trwały 3,74 s (486 tików/s), czyli
około 7,5 razy krócej. Pozostałe czasy obejmują też zapis i obsługę gry;
pomiar nie rozdziela obliczeń silnika od oczekiwania w `advance_action`.

Po zmianie powtórzono serię 100 seedów bota etykietowego: 66346 tików
w 125,26 s (529,7 tiku/s). We wszystkich próbach liczby zabitych, zgony,
nagrody, czasy i odciski obrazów odpowiadały poprzedniej serii
`porownanie_demony.csv` (zgony i nagrody sprawdzono na podstawie jej opisu
oraz liczby zabitych). Pięć prób bota losowego porównano bezpośrednio przed
zmianą dokładności zegara i po niej: wyniki i odciski obrazów były identyczne,
a seedy sprawdzono w powtórkach. Wyniki wydajności zależą od komputera.

## Analiza najgorszej próby defend_the_center

**Sprostowanie:** wcześniejsza analiza poniżej pominęła demona. Dziennik
zawiera etykietę `Demon` o identyfikatorze 7 już w tiku 75; około tiku 88
znajdował się przy środku obrazu, a bot dalej obracał się w prawo. Ten sam
obiekt ponownie pojawił się przy prawej krawędzi w tikach 268–271, przed
śmiercią w tiku 272. Kod uwzględniał tylko `MarineChainsawVzd` i ignorował
demony. Dziennik nie identyfikuje źródła ostatniego obrażenia.

## Porównanie po poprawce rozpoznawania demonów

Na tych samych 100 seedach porównano zapisaną wcześniej serię starego bota
z nową serią. Nowy bot rozpoznaje `Demon` i daje mu pierwszeństwo przed
`MarineChainsawVzd`. Seedy sprawdzono w nagłówkach wszystkich 200 powtórek;
nowa seria ma 100 różnych odcisków obrazów. Każda nowa gra ma powtórkę,
dziennik i wideo. Dane par są w `porownanie_demony.csv`.

| Wynik | Stary bot | Nowy bot |
|---|---:|---:|
| Średnio zabitych | 8,63 | 10,01 |
| Średni czas (tiki) | 536,92 | 663,46 |
| Zakres zabitych | 5–11 | 8–12 |

Na 74 seedach nowy bot zabił więcej, na 16 tyle samo, a na 10 mniej.
Wszystkie 100 nowych gier skończyło się ze zdrowiem poniżej lub równym 0.
Na seedzie 146 wynik wzrósł z 5 do 10 zabitych, a czas z 272 do 948 tików.
Powtórka, dziennik i wideo z nowej serii mają nazwę bazową
`center_etykiety_146_20261114_184151_031660` w `powtorki/`.

## Wcześniejsza analiza próby (przed sprostowaniem)

W poprzednich 100 próbach bota celującego minimum to 5 zabitych (dwa razy).
Jako najgorszą wybrano krótszą z nich: seed wejściowy 146, 272 tiki.
Ponowne uruchomienie tego seeda dało ten sam wynik: 5 zabitych, śmierć
w 272. tiku i 8 pocisków na końcu. Powtórka, dziennik i wideo nowej próby:
`center_etykiety_146_20261114_181038_372764` w `powtorki/`.

Trzeciego przeciwnika bot zabił w 105. tiku, a czwartego dopiero w 231.
W tym czasie życie spadło ze 100 do 80 w tiku 170, do 72 w 198 i do 12
w 224; końcowy cios sprowadził je do -4. Bot stoi w miejscu i strzela
również podczas szukania celu, więc długo wystawiał się na ataki. Dziennik
pokazuje widoczne etykiety, ale nie wskazuje źródła obrażeń ani trafień,
dlatego nie rozstrzyga, który przeciwnik zadał każdy cios ani czemu każdy
strzał nie trafił. To analiza tej jednej próby, nie dowód przyczyn różnic
we wszystkich seedach.
- 2026-11-13 21:37 — MAP01: **3720 tików** (106,29 s czasu gry); dawny pomiar zegarowy 105,45 s; powtórka: `recznie_20261113_213739.lmp`
- 2026-11-13 21:45 — MAP01: **3027 tików** (86,49 s czasu gry); dawny pomiar zegarowy 85,88 s; powtórka: `recznie_20261113_214524.lmp`

Czasy odczytano przez odtworzenie powtórek w ViZDoom 1.3.2 na Freedoom 2 MAP01, zliczając jednokrokowe `advance_action` do końca. Obie zakończyły się bez śmierci; brak osobnego sygnału wyjścia w archiwalnym zapisie, więc kwalifikacja opiera się także na ówczesnym opisie ukończenia. Poziom trudności i seed pierwotnych prób nie zostały udokumentowane.

# defend_the_center — poprawione porównanie (2026-11-14)

100 prób na bot, ten sam zestaw 100 seedów silnika dla obu botów. Każda gra
ma powtórkę w `powtorki/`. Szczegóły i SHA-256 kolejnych obrazów widzianych
przez bota zapisano w `porownanie.csv`. Sprawdzono 200 powtórek: w każdej
z dwóch serii jest 100 różnych seedów silnika, 100 różnych odcisków obrazów
oraz 100 różnych plików powtórek. Seed silnika sprawdzono w nagłówku każdej
powtórki. Powtórki nie są przechowywane w Git.

| Bot | Próby | Średnio zabite potwory | Średnio zgony | Średnia nagroda | Średni czas (tiki) |
|---|---:|---:|---:|---:|---:|
| Celowanie po etykietach ekranowych | 100 | 8,63 | 1,00 | 7,63 | 536,9 |
| Losowy | 100 | 1,64 | 1,00 | 0,64 | 351,7 |

Przykład różnych gier bota celującego:

| Seed wejściowy | Seed silnika w powtórce | Zabite | Tiki | Początek SHA-256 obrazów |
|---:|---:|---:|---:|---|
| 1 | 1791095845 | 8 | 634 | `273ed1c328fbbb96` |
| 2 | 1872583848 | 8 | 474 | `b006242db4a91bce` |
| 5 | 953453411 | 5 | 286 | `b3b91f972b590a0b` |

Poprzednie porównanie (średnie 8,79 i 1,45 zabitego) jest niewiarygodne:
różne seedy wejściowe nie gwarantowały różnych gier. Na Windows wartości seeda
silnika większe od 2147483647 były ograniczane do 2147483647. Na przykład
w teście diagnostycznym seedy 0, 3 i 4 dały identyczną powtórkę i wynik
9 zabitych / 462 tiki. Poprawiony skrypt dobiera seedy bez tego przepełnienia,
a rzeczywisty seed weryfikuje w nagłówku powtórki.
# Okno startowe ViZDoom (2026-11-14)

Monitor zdarzeń okien Windows wykrył przed zmianą dwukrotne wyświetlenie
`ViZDoomMainWindow` przez `vizdoom.exe` na pulpicie Default. Po przeniesieniu
procesu skryptu i silnika na osobny pulpit nie wykrył tam okna silnika
podczas MAP01, obu botów defend_the_center ani próby ręcznej. Okno Pygame
gry ręcznej pojawiło się na widocznym pulpicie; próbę przerwano, zapisując
powtórkę. Monitor obserwował zdarzenia systemowe, nie jest nagraniem ekranu.

Porównanie przed i po dla seeda 1: MAP01 zakończyła się wyjściem w 601 tikach
z 74 punktami życia, a całe dzienniki JSONL były identyczne. W defend_the_center
bot celujący uzyskał 21 zabójstw, 1 zgon, nagrodę 20 i 1013 tików, a losowy
1 zabójstwo, 1 zgon, nagrodę 0 i 432 tiki; odciski obrazów też były identyczne.
To porównanie jednego seeda, nie wszystkich możliwych gier.
