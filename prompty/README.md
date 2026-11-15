# Prompty z filmu, po kolei

Każdy prompt jest tu w takim brzmieniu, w jakim poszedł do agenta (aplikacja Codex, tryb „Poproś o zatwierdzenie”, rozumowanie „Średni”). Pisane są jak od laika: mówią, co widać i czego chcę, a nie jak to naprawić. Przy każdym jest model, czas pracy agenta, wynik i tag, pod którym w tym repozytorium leży stan projektu po tym kroku (`git checkout <tag>`).

Część promptów zaczyna się od zdania „To dalszy ciąg projektu…”, bo szły do nowego czatu, który nie zna poprzedniego.

## Etap 1. Start

- Model: GPT-6 Luna (plan darmowy)
- Czas pracy agenta: 13 minut nagrania, 6 próśb o zgodę
- Wynik: gra uruchamia się w oknie
- Tag: `etap-1`

> Chcę zrobić bota, który sam gra w Dooma. Będzie to zwykły skrypt w Pythonie, bez uczenia maszynowego i bez modelu AI w trakcie gry. Użyj biblioteki ViZDoom i darmowego Freedooma, który jest w jej paczce. Pracuj tylko w tym folderze. Załóż repozytorium Git i osobne środowisko Pythona. Po każdym działającym kroku rób commit z krótkim opisem po polsku. Każdą grę zapisuj jako powtórkę w folderze powtorki. Na początek uruchom pierwszy poziom Freedoom 2 (MAP01) w oknie i pokaż, że działa. Pisz do mnie po polsku i krótko.

## Etap 2. Najpierw ja

- Model: GPT-6 Luna
- Czas pracy agenta: 58 minut nagrania, 16 commitów
- Wynik: tryb ręczny po kilku poprawkach; czasy człowieka 105,45 s i 85,88 s (3720 i 3027 tików)
- Tag: `etap-2`

> Zrób mi tryb, w którym sam przechodzę MAP01 na klawiaturze i myszy, w oknie. Program ma zmierzyć mój czas od startu do naciśnięcia przełącznika wyjścia i zapisać wynik do pliku wyniki.md. Potem zapisz w pliku cel.md, że bot ma przejść ten poziom szybciej ode mnie.

## Etap 3. Pierwszy bot

- Model: GPT-6 Luna
- Czas pracy agenta: 65 minut nagrania, 9 commitów
- Wynik: bot celujący 8,79 zabitych, losowy 1,45; później okazało się, że 47 ze 100 gier to ta sama gra
- Tag: `etap-3`

> To dalszy ciąg projektu z tego folderu: bota, który sam gra w Dooma. Najpierw przeczytaj pliki i historię commitów. Zasady są te same co od początku. Bot to zwykły skrypt w Pythonie, bez uczenia maszynowego i bez modelu AI w trakcie gry. Używamy biblioteki ViZDoom i darmowego Freedooma z jej paczki. Pracuj tylko w tym folderze, w istniejącym repozytorium Git i środowisku Pythona. Po każdym działającym kroku rób commit z krótkim opisem po polsku. Każdą grę zapisuj jako powtórkę w folderze powtorki. Pisz do mnie po polsku i krótko. Zapisz te zasady w projekcie tak, żeby każdy nowy czat je znał.
>
> Teraz pierwszy bot, na prostszym scenariuszu defend_the_center z ViZDoom. Bot ma widzieć tylko to, co jest na ekranie, czyli etykiety obiektów, ma celować i strzelać. Zrób też bota losowego i porównaj oba na 100 próbach z różnymi seedami, bez okna. Wynik dopisz do wyniki.md jako tabelę.

## Krok 3B. Czy to 100 różnych gier

- Model: najpierw GPT-6 Luna, potem GPT-6.1 Terra (plan Plus), ten sam prompt z tego samego commita
- Czas pracy agenta: Luna 33 min 30 s, Terra 16 min 16 s
- Wynik: Luna odpowiedziała „tak” wbrew liczbom i niczego nie naprawiła; Terra znalazła błąd biblioteki na Windowsie (obcinany numer gry) i poprawiła test: 8,63 do 1,64
- Tag: `krok-3b`

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> W porównaniu botów z wyniki.md coś mi się nie zgadza: wiele prób ma identyczny wynik, 9 zabitych potworów i 462 tiki. Sprawdź, czy 100 prób to na pewno 100 różnych gier. Jeśli nie, znajdź przyczynę, popraw test i powtórz porównanie. Pokaż mi dowód, że gry są różne.

## Krok 3C. Audyt

- Model: GPT-6.1 Terra
- Czas pracy agenta: około 52 sekund
- Wynik: siedem problemów, bez zmian w kodzie
- Tag: brak, ten krok niczego nie zmienił w repozytorium

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> Zanim pójdziemy dalej, zrób audyt całego projektu. Sprawdź krytycznie kod, wyniki w wyniki.md, opisy w README i cel w cel.md. Chcę wiedzieć, czemu z tego mogę ufać, a czemu nie, i co trzeba poprawić, zanim bot zacznie przechodzić MAP01 na czas. Niczego nie zmieniaj i nie rób commitów. Daj mi listę problemów od najważniejszego, każdy z krótkim dowodem.

## Krok 3D. Poprawki po audycie

- Model: GPT-6.1 Terra
- Czas pracy agenta: 2 min 35 s
- Wynik: jedna miara czasu dla człowieka i bota: tiki gry; poprzeczka 3027 tików
- Tag: `krok-3d`

> Zgadzam się z audytem. Zanim pójdziemy dalej, popraw punkty 3 i 5: ustal jedną miarę czasu, taką samą dla mnie i dla bota, przelicz na nią moje dwa przejścia z zapisanych powtórek i zapisz zasady pojedynku w cel.md. Popraw też opisy z punktów 6 i 7. Bota jeszcze nie ruszaj. Pokaż mi, co się zmieniło.

## Etap 4. Co ten bot robi

- Model: GPT-6.1 Terra
- Czas pracy agenta: 3 min 17 s
- Wynik: zapis każdej gry i wideo; wyjaśnienie najgorszej próby pomija różowego demona
- Tag: `etap-4`

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> Nie wiem, co robi bot w defend_the_center i czemu w jednych grach zabija 11 potworów, a w innych tylko 5. Dodaj zapis każdej gry do pliku: co widział, co zrobił, ile miał życia i amunicji. Dodaj też nagrywanie gry do pliku wideo. Znajdź najgorszą próbę, nagraj ją i powiedz mi, czemu poszła źle.

## Krok 4B. Różowy potwór

- Model: GPT-6.1 Terra
- Czas pracy agenta: kilka minut i 100 gier
- Wynik: bot celuje także w demony: 8,63 na 10,01 zabitych
- Tag: `krok-4b`

> Obejrzałem nagranie. Widzę różowego potwora, od którego bot się odwraca i w ogóle do niego nie strzela, a na końcu ten potwór go zagryza. W Twoim wyjaśnieniu go nie ma. Sprawdź to w dzienniku. Jeśli to prawda, popraw bota i porównaj starą i nową wersję na tych samych 100 seedach.

## Etap 5. Szybkość

- Model: GPT-6.1 Terra
- Czas pracy agenta: 7 min 3 s
- Wynik: 100 gier w około 2 minuty zamiast 17, z identycznymi wynikami
- Tag: `etap-5`

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> Ostatnie porównanie 100 prób w defend_the_center trwało około 17 minut. Sprawdź, ile kroków gry na sekundę robi bot bez okna i na co schodzi czas. Znajdź, co hamuje, i przyspiesz to. Sprawdź też, czy po zmianie wyniki są takie same jak przed nią.

## Krok 4C. Bot trzyma strzał

- Model: GPT-6.1 Terra
- Czas pracy agenta: 4 min 15 s
- Wynik: średnia 10,01 na 11,06, ale w 46 grach na 100 gorzej (regresja)
- Tag: `krok-4c`

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> Na nagraniach gier bota w defend_the_center widzę, że strzela bez przerwy, także wtedy, gdy nie ma nikogo na celowniku. Sprawdź w dziennikach, ile naboi marnuje i kiedy mu się kończą. Popraw to i porównaj z obecną wersją na tych samych 100 seedach.

## Krok 4D. Ginie z nabojami

- Model: GPT-6.1 Terra
- Czas pracy agenta: około 5 minut
- Wynik: martwa strefa celowania usunięta: 22,82 zabitych na 26 naboi
- Tag: `krok-4d`

> Coś tu nie gra. Po poprawce wynik spadł na 46 seedach, a bot zużywa średnio tylko 15,78 z 26 nabojów, czyli ginie z amunicją w magazynku. Znajdź grę, w której poszło mu najgorzej, nagraj ją i sprawdź w dzienniku, co robi, kiedy widzi potwora i nie strzela. Popraw to i porównaj wszystkie trzy wersje na tych samych 100 seedach.

## Etap 6. Prawdziwy cel

- Model: GPT-6.1 Terra
- Czas pracy agenta: 11 min 3 s
- Wynik: bot biegnie do wyjścia w 601 tików (17 s), nie strzela, dochodzi w 8 grach na 20
- Tag: `etap-6`

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> Teraz prawdziwy cel z cel.md. Bot ma sam przejść MAP01 od startu do przełącznika wyjścia, w mniej tików niż mój najlepszy wynik z wyniki.md. Dalej zwykły skrypt, bez uczenia maszynowego. Bot może wiedzieć to, co wie gracz, który zna ten poziom na pamięć: całą mapę oraz ile jest potworów, jakie i gdzie stoją na starcie. W trakcie gry może wiedzieć to, co widać na ekranie, gdzie sam stoi i w którą stronę patrzy. Nie może podglądać, gdzie są teraz potwory, których nie widać, odtwarzać nagranych ruchów ani ułatwiać sobie gry: ten sam poziom trudności co u mnie, bez kodów i bez wyłączania potworów. Popraw te zasady w cel.md. Zaplanuj to po kolei i zacznij od najprostszej wersji. Sam uruchamiaj testy na różnych seedach i poprawiaj, aż bot dojdzie do wyjścia. Każdą próbę nagrywaj tak jak dotąd, żebym mógł ją obejrzeć.

## Krok 6B. Wyskakujące okno

- Model: GPT-6.1 Terra
- Czas pracy agenta: 5 min 59 s
- Wynik: okno startowe silnika przeniesione na niewidoczny pulpit
- Tag: `krok-6b`

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> Przy każdym uruchomieniu gry na chwilę wyskakuje mi na ekranie małe okno z tekstem. Prosiłem o granie bez okna i to mnie rozprasza. Znajdź, skąd bierze się to okno, i zrób tak, żeby nie wyskakiwało przy żadnym skrypcie z tego projektu. Pokaż mi, jak sprawdziłeś, że już nie wyskakuje, i czy wyniki gier się nie zmieniły.

## Krok 6C. Bot gra jak gracz

- Model: GPT-6.1 Terra
- Czas pracy agenta: 16 min 9 s
- Wynik: bot walczy i zbiera: 14 wyjść na 20 (16 na 20 na seedach niezależnych), około 1800 tików
- Tag: `krok-6c`

> Obejrzałem nagrania. Bot biegnie prosto do wyjścia, do nikogo nie strzela i niczego nie zbiera, a w części gier ginie po drodze. Chcę, żeby grał jak gracz: walczył z potworami, które stoją mu na drodze, i zbierał po drodze apteczki, pancerz i amunicję. Może znać stałe fakty gry: bronie, potwory i znajdźki. W nagraniach pokaż interfejs z życiem i amunicją. Sprawdź starą i nową wersję na tych samych 20 różnych seedach: ile razy każda dochodzi do wyjścia, ile razy ginie i w ile tików. Dalej ma być szybszy niż moje 3027 tików.

## Etap 7. Testy i dowód

- Model: GPT-6.1 Terra
- Czas pracy agenta: około 8 minut nagrania
- Wynik: jedno polecenie sprawdza wszystko; 16 wyjść na 20 nowych seedach, mediana 1867 tików
- Tag: `etap-7`

> Na koniec dowód. Zrób jedno polecenie, które sprawdza wszystko: defend_the_center i MAP01. MAP01 sprawdź na 20 nowych seedach, których nie używałeś do poprawiania bota. Ma pokazać, ile razy bot naprawdę doszedł do wyjścia, ile razy zginął, ile razy skończył mu się czas, oraz medianę czasu. Nagraj najlepszą próbę do pliku wideo.

## Krok 7B. Strzelba i kręcenie przy wyjściu

- Model: GPT-6.1 Terra
- Czas pracy agenta: 26 min 59 s
- Wynik: kręcenie przy wyjściu naprawione; strzelba z podłogi dalej nie jest podnoszona; dwie gry utknęły (regresja)
- Tag: `krok-7b`

> Obejrzałem najlepszą próbę. Dwie rzeczy mi nie pasują. Bot przebiega obok strzelby, która leży na podłodze, i jej nie podnosi, a strzelba jest lepsza od pistoletu. Pod koniec kręci się w kółko przed wyjściem, zanim naciśnie przełącznik. Sprawdź obie rzeczy w dziennikach, popraw je i porównaj starą i nową wersję na tych samych 20 seedach z dowodu, a potem na 20 kolejnych nowych.

## Krok 7C. Strzelba z podłogi i utknięcia

- Model: GPT-6.1 Terra
- Czas pracy agenta: 33 min 26 s
- Wynik: strzelba leży na podwyższeniu, bot wchodzi po stopniach; 88 wyjść na 100 gier
- Tag: `krok-7c`

> Obejrzałem nowe nagranie i tabelę. Dwie rzeczy dalej mi nie pasują. Bot nadal przebiega obok strzelby, która leży na podłodze przy trasie, i bierze strzelbę dopiero od zabitego przeciwnika. A w kilku grach utknął w jednym miejscu i stał tak do końca czasu, choć poprzednia wersja te gry przechodziła. Znajdź w dziennikach, gdzie i dlaczego utknął, popraw obie rzeczy i sprawdź wynik na wszystkich 60 seedach oraz na 20 nowych kontrolnych.

## Krok 7D. Bot ma nie ginąć

- Model: GPT-6.1 Sol
- Czas pracy agenta: około 47 minut
- Wynik: bot nie wysadza się już na beczkach: 99 wyjść na 100 odłożonych seedach (98 na 100 na niezależnych)
- Tag: `krok-7d`

> To dalszy ciąg projektu z tego folderu. Najpierw przeczytaj AGENTS.md, pliki i historię commitów.
>
> Bot przechodzi MAP01 szybciej ode mnie, ale w ostatniej tabeli w wyniki.md dalej ginie: 9 razy na 80 gier. Chcę, żeby dochodził do wyjścia w każdej grze. Sprawdź w dziennikach i na nagraniach, gdzie i dlaczego ginie, i popraw to tak, żeby nie zepsuć reszty. Zasady z cel.md zostają bez zmian, a bot dalej ma być szybszy niż moje 3027 tików. Zanim cokolwiek poprawisz, odłóż 100 nowych seedów i nie używaj ich do poprawiania. Na koniec porównaj starą i nową wersję na dotychczasowych 80 seedach i na tych 100 odłożonych: ile wyjść, ile zgonów, ile razy skończył się czas i mediana tików.

## Etap 8. Następny poziom

- Model: GPT-6.1 Sol
- Czas pracy agenta: około 4,5 minuty
- Wynik: ten sam bot na drugim poziomie (MAP02): 0 wyjść na 20 gier
- Tag: `etap-8`

> Na koniec jedna próba z ciekawości. Wpuść tego samego bota na następny poziom, MAP02. Zagraj 20 gier na różnych seedach i jedną nagraj do pliku wideo. Niczego w bocie nie poprawiaj. Powiedz mi krótko, co się stało i dlaczego.
