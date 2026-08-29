# Sprint 6 — końcowe review G0/G1/G2.1

**Data review:** 29 sierpnia 2026, 22:51 CEST

**Rola review:** `gpt-5.6-sol/high`

**Reviewowany commit:** `5f71a71b5dc5d1d59d96f83034e34ed0309608bf`

**Decyzja:** `APPROVED_TO_CREATE_SEPARATE_PROTECTED_OPEN_APPROVAL`

**Protected evidence podczas review:** zamknięte; zero odczytanej treści, zero
inferencji i zero utworzonej autoryzacji.

## Executive conclusion

Pakiet G0/G1/G2.1 jest spójny i wystarczający do utworzenia osobnego artefaktu
`APPROVED_TO_OPEN_PROTECTED_SPLITS`. Approval nie otwiera danych samodzielnie:
jednorazowy run nadal wymaga jawnego parametru operatora. Nie znaleziono
blockera technicznego ani metodologicznego dla wykonania evidence runu na
obecnym, zamrożonym stanowisku.

## Review G0 — Evidence Contract Freeze

- decyzja `S6_G0_PASS`, wszystkie kontrole true,
- 8/8 zamrożonych hashy kontraktów i schema zgodnych z bieżącymi plikami,
- trzy adaptery mają zgodne konfiguracje, model bazowy i zweryfikowane pliki,
- primary protected inputs sprawdzono wyłącznie metadanymi; treści nie czytano,
- analityczny kontrakt pozostaje niezmieniony w stanie HOLD,
- tag `s6-g0-pass` istnieje i wskazuje commit
  `e54fe925a86d16e242e8994b1382d02ce5186040`.

**Wniosek G0:** PASS bez zastrzeżenia.

## Review G1 — Shadow Freeze

- decyzja `S6_G1_PASS`, wszystkie kontrole mechaniczne i human/SME true,
- dataset i source pack mają hashe zgodne jednocześnie z registry, review i
  raportem G1,
- 50/50 przypadków zostało przejrzanych i zaakceptowanych przez człowieka/SME,
- zero krytycznych uwag; dokładnie 10 przypadków na każdy status i rodzinę
  ryzyka,
- shadow jest oznaczone jako risk-directed, a nie primary independent evidence,
- tag `s6-g1-pass` istnieje i wskazuje commit
  `a46a92bf78424e3044774f53a51a05a1dccc8d30`.

**Wniosek G1:** PASS bez zastrzeżenia.

## Review G2.1 — Technical Readiness Hardening

- decyzja `S6_G2_1_PASS`, 17/17 kontroli true,
- 87/87 testów PASS oraz 13/13 komórek trzech notebooków wykonanych przy
  `RUN_TRAINING=False`,
- dokładna rewizja modelu została rozwiązana local-only; 3/3 shardy,
  398 wpisów indeksu i 8 044 982 000 bajtów wag zweryfikowane,
- 4/4 kontrolowane awarie weszły w obsługę wyjątku i wykonały fallback,
- niezależnie od raportu zrekonstruowano rejestr zakazanych źródeł z
  `sprint4_matrix_v1.json` i `shadow_registry.json`: przeskanowano 9 źródeł
  treningowych we wszystkich `qlora*.json`, wykryto 0 naruszeń,
- 23/23 pliki wymagane przez kontrakt approval istnieją,
- tag `s6-g2.1-pass` istnieje i wskazuje commit
  `5f71a71b5dc5d1d59d96f83034e34ed0309608bf`.

**Wniosek G2.1:** PASS z ograniczeniami operacyjnymi opisanymi poniżej.

## Niezamknięte ograniczenia — nieblokujące dla tego runu

1. Próba czystego venv buduje i instaluje projekt offline z `--no-deps`.
   Pełnego wheelhouse zależności nie ma w repozytorium. Evidence run należy
   wykonać w obecnym `.venv`, z istniejącym cache modelu i adapterami. Zmiana
   maszyny lub odtworzenie środowiska od zera wymaga ponownego G2.
2. Scenariusz OOM sprawdza rzeczywistą obsługę wyjątku i integralność fallbacku,
   lecz nie uruchamia automatycznie mniejszego modelu. Podczas evidence runu OOM
   oznacza przerwanie i wznowienie identycznego runu ze zweryfikowanego
   artefaktu; nie wolno zmieniać modelu, promptu ani parametrów jakościowych.
3. PASS dotyczy gotowości warsztatu na danych syntetycznych. Nie jest zgodą
   produkcyjną ani walidacją rozwiązania na danych banku.

## Warunki approval i wykonania

- osobny approval musi wiązać dokładne hashe 23 plików kontraktu,
- approval wskazuje reviewowany commit i pozostawia
  `operator_confirmation_required=true`,
- przed uruchomieniem Git musi być czysty, a wszystkie wymagane tagi obecne,
- operator uruchamia dokładnie jeden evidence run przez jawny parametr,
- kolejność jest stała: original 100×3, boundary 120×3, challenge 20×3,
  shadow 50×3,
- nie wolno trenować, retunować, zmieniać promptu, guarda, goldów ani progów po
  zobaczeniu wyników,
- awarię techniczną wolno wznowić wyłącznie jako identyczny run; porażkę
  jakościową należy zaraportować bez naprawczego rerunu,
- po inferencji nadal obowiązuje manual review 60/60 primary challenge i
  150/150 shadow responses.

## Test blokady

Runner uruchomiony z parametrem operatora, lecz bez approval, zatrzymał się z
komunikatem `Brak poprawnego, osobnego approval Sol/high dla protected
evidence.` Nie utworzył pliku autoryzacji i nie odczytał protected content.

## Decyzja końcowa

Utworzyć osobny artefakt `results/sprint6/protected_open_approval.json` z
decyzją `APPROVED_TO_OPEN_PROTECTED_SPLITS`, dokładnymi bindingami bieżącego
pakietu i powyższymi ograniczeniami. Sam artefakt nie konsumuje potwierdzenia
operatora i nie uruchamia inferencji.
