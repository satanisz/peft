# Sprint 6 — raport G2.1B Technical hardening

**Data:** 29 sierpnia 2026

**Model wykonawczy:** Luna/low

**Decyzja:** `S6_G2_1_PASS`

**Protected evidence:** zamknięte; zero odczytanej treści i zero inferencji.

## Wynik

G2.1B zastąpiło deklaratywne kontrole rzeczywistym wykonaniem ścieżek
technicznych. Wszystkie 17 kontroli przeszło:

- 87 testów jednostkowych: PASS,
- 3 notebooki i 13/13 komórek kodu wykonane, `RUN_TRAINING=False`,
- dokładna rewizja `cdbee75f17c01a7cc42f958dc650907174af0554`
  rozwiązana wyłącznie lokalnie,
- 3/3 shardy `safetensors`, 398 wpisów indeksu i 8 044 982 000 bajtów wag
  zweryfikowane; zero brakujących shardów, pustych plików i tensorów,
- projekt zbudowany i zainstalowany bez sieci w nowym, tymczasowym venv;
  zależności nie były ponownie rozwiązywane, ponieważ ich pełny wheelhouse nie
  jest częścią repozytorium,
- cztery kontrolowane awarie faktycznie weszły w obsługę wyjątku i wykonały
  zweryfikowany fallback,
- wszystkie źródła treningowe ze wszystkich konfiguracji `qlora*.json`
  przeskanowane; zero użyć protected lub shadow datasetów.

## Wykonane scenariusze awarii

| Scenariusz | Rzeczywisty wyjątek | Wykonany fallback | Wynik |
|---|---|---|---|
| OOM | `torch.OutOfMemoryError` | adapter zgodny z manifestem 7/7 | PASS |
| brak rewizji modelu | `LocalEntryNotFoundError` | exact revision local-only | PASS |
| brak checkpointu | `FileNotFoundError` | ostatni adapter zgodny z manifestem | PASS |
| niedostępna sieć | `ConnectionError` | exact revision local-only | PASS |

Wstrzyknięcie OOM nie alokowało pamięci GPU. Celem było wykonanie rzeczywistej
obsługi błędu i fallbacku, nie destabilizacja stanowiska prowadzącego.

## Granica twierdzenia offline

PASS potwierdza, że zamrożone środowisko warsztatowe uruchamia dokładną rewizję
modelu z kompletnymi wagami bez sieci oraz że sam projekt daje się zbudować,
zainstalować i zaimportować offline w czystym venv. Nie potwierdza odtwarzania
wszystkich zależności od zera na nowej maszynie: repozytorium nie zawiera
pełnego wheelhouse. Na szkolenie nadal należy zachować działające `.venv`, cache
modelu i adaptery albo przygotować osobny pakiet instalacyjny.

## Kontrakt po G2.1

Osobny kontrakt approval i runner wymagają teraz decyzji
`S6_G2_1_PASS`. Zamrożony analityczny kontrakt G0 pozostaje niezmieniony w
stanie HOLD. Nie utworzono approval ani autoryzacji protected runu.

## Następny krok

Po commicie i tagu `s6-g2.1-pass` wymagany jest review Sol/high całego pakietu
G0/G1/G2.1. Dopiero osobny artefakt
`APPROVED_TO_OPEN_PROTECTED_SPLITS`, wiążący dokładne hashe, może poprzedzić
jednorazowe jawne potwierdzenie operatora. Sam PASS G2.1 niczego nie otwiera.
