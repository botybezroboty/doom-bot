# Wyniki gry ręcznej
- 2026-11-13 21:37 — MAP01: **105.45 s** (ukończono 21:39); powtórka: `recznie_20261113_213739.lmp`
- 2026-11-13 21:45 — MAP01: **85.88 s** (ukończono 21:46); powtórka: `recznie_20261113_214524.lmp`

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
