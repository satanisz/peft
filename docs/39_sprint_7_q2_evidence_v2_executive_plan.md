# Sprint 7 — Q2 i Evidence v2: plan odzyskania jakości

## 1. Decyzja wykonawcza

Protected Evidence v1 pozostaje niezmiennie `FAILED / FROZEN / READ-ONLY`.
Sprint 7 nie jest rerunem, poprawką ani próbą zmiany tej decyzji. Jest nowym
projektem badawczym, który wykorzystuje błędy v1 jako materiał diagnostyczny,
ale wymaga nowych danych treningowych, nowych goldów oraz wcześniej
niewidzianego Evidence v2.

Kolejność jest celowa: najpierw naprawiamy system na train/dev, potem — tylko
jeśli bramki przejdą — zamrażamy i jednokrotnie otwieramy Evidence v2.

## 2. Podział odpowiedzialności modeli

| Rodzaj pracy | Model | Dlaczego |
|---|---|---|
| analiza błędów, kontrakt, progi, decyzje o danych/prompt/guard | Sol/high | wymaga syntezy, oceny ryzyka i kontroli leakage |
| authoring goldów i końcowe review | Sol/high + człowiek/SME | model wspiera; człowiek zatwierdza semantykę i ryzyko |
| walidatory, generowanie według zamrożonej specyfikacji, testy | Luna/low | praca mechaniczna i powtarzalna |
| trening, inferencja, monitoring i agregacja | Luna/low | długie wykonanie według zamrożonej konfiguracji |
| decyzja o otwarciu Evidence v2 i interpretacja wyniku | Sol/high + operator | decyzja nie może wynikać automatycznie z samego runnera |

Luna/low nie zmienia progów, goldów, hiperparametrów ani listy seedów po
rozpoczęciu biegu. Błąd lub słaby wynik wraca do Sol/high.

### Executive timeline

| Sprint | Właściciel wykonania | Orientacyjnie | Decyzja końcowa |
|---|---|---:|---|
| S7.0–S7.1 | Sol/high | 1,5–2,5 dnia | zatwierdzony projekt naprawczy |
| S7.2 | Sol/high + SME, Luna/low | 2–4 dni | zamrożone train/dev v2 |
| S7.3 | Luna/low, review Sol/high | 1–2 dni | czy wystarcza system-first fix |
| S7.4 | Luna/low, freeze/review Sol/high | 1–2 dni + GPU | Q2 dev PASS albo FAIL |
| S7.5 | Sol/high + SME, walidacja Luna/low | 2–4 dni | Evidence v2 frozen/unopened |
| S7.6 | Luna/low, approval Sol/high | 0,5–1 dnia | approval albo HOLD |
| S7.7 | Luna/low, decyzja Sol/high | 1 dzień + GPU | closure Evidence v2 |
| S7.8 | Sol/high + Luna/low | 0,5–1 dnia | opcjonalny release badawczy |

Łącznie: około 9–14 dni roboczych plus kolejki GPU i review SME. S7.4–S7.8 są
warunkowe; projekt może zakończyć się wcześniej na uczciwym FAIL albo na
decyzji, że prompt+guard jest lepszym rozwiązaniem niż kolejny adapter.

## 3. Sprinty i bramki

### S7.0 — otwarcie projektu i zamrożenie baseline

**Model:** Sol/high. **Czas:** 0,5 dnia.

- potwierdzenie hashy closure v1, wyników i adapterów Q1;
- manifest wykorzystanych artefaktów historycznych;
- rejestr zbiorów zakazanych w treningu Q2;
- jednoznaczne oznaczenie v1 jako materiału diagnostycznego;
- plan gałęzi, artefaktów i nazw nowych wersji.

**Bramka:** `S7_BASELINE_FROZEN`. Bez niej nie tworzymy danych v2.

### S7.1 — analiza przyczyn i docelowa architektura decyzji

**Model:** Sol/high. **Czas:** 1–2 dni.

- analiza wszystkich błędów v1 per przypadek i seed;
- osobne koszyki: `INSUFFICIENT_DATA`, `NOT_APPLICABLE`, false `PASS`,
  `severity`, `source_id`, injection i deterministic mismatch;
- rozdzielenie remedium na: dane, prompt, guard, kontrakt i human review;
- określenie, czego model nie powinien rozstrzygać;
- projekt prompt v3, decision guard v2 i source-integrity guard v2;
- hipotezy eksperymentalne i metryki kosztu błędu.

**Bramka:** `S7_REMEDIATION_DESIGN_APPROVED`. Wynikiem nie jest jeszcze nowy
adapter.

**Status:** wykonane. Raport: `docs/40_sprint_7_0_7_1_baseline_and_remediation_report.md`.

### S7.2 — train/dev v2 bez nowego protected evidence

**Projekt:** Sol/high + człowiek/SME. **Wykonanie:** Luna/low. **Czas:** 2–4 dni.

Planowany minimalny pakiet:

- 240–360 nowych przykładów hardening do treningu;
- 90 nowych przypadków dev-hard v2;
- co najmniej 30 par kontrfaktycznych, w których zmienia się jedna przesłanka;
- nadreprezentacja `INSUFFICIENT_DATA`, `NOT_APPLICABLE` i bezpiecznej
  eskalacji zamiast zgadywania;
- jawne hard negatives dla source integrity i prompt injection;
- rejestr provenance oraz skaner podobieństwa/leakage.

Goldy dev mogą być używane iteracyjnie. Nie mogą później pełnić roli Evidence
v2. Każdy przypadek ma kryterium decyzji, severity, dozwolone źródła i powód
eskalacji.

**Bramka:** `S7_TRAIN_DEV_V2_FROZEN` po walidacji mechanicznej i review SME.

**Status projektu Sol/high:** `S7_2_DESIGN_READY_FOR_LUNA_LOW`. Specyfikacja i
handoff: `docs/41_sprint_7_2_design_and_luna_handoff.md`. Dane nie zostały
jeszcze wygenerowane, a bramka końcowa S7.2 pozostaje otwarta.

### S7.3 — system-first ablation na dev

**Projekt i review:** Sol/high. **Wykonanie:** Luna/low. **Czas:** 1–2 dni.

Najpierw porównujemy bez nowego treningu:

1. Q1 + prompt v2 — baseline historyczny;
2. Q1 + prompt v3;
3. Q1 + prompt v3 + decision guard v2;
4. Q1 + prompt v3 + decision guard v2 + source guard v2.

Każdy wariant korzysta z tych samych przypadków dev, seedów, parametrów
dekodowania i agregacji. Raport pokazuje wynik surowego LLM i wynik systemu po
guardzie osobno. Guard może blokować lub eskalować; nie może po cichu przepisać
odpowiedzi na oczekiwany gold.

**Bramka:** `S7_SYSTEM_ABLATION_REVIEWED`. Sol/high decyduje, czy potrzebny
jest Q2. Jeśli prompt+guard wystarczają, nie trenujemy dla samego treningu.

### S7.4 — kontrolowany trening Q2

**Freeze konfiguracji:** Sol/high. **Trening i monitoring:** Luna/low.
**Czas:** 1 dzień przygotowania + około 4–6 godzin GPU dla trzech seedów,
zależnie od ostatecznej liczby kroków.

- jedna zamrożona konfiguracja QLoRA i trzy seedy;
- train wyłącznie z rejestru S7.2;
- zero protected/shadow v1 oraz przyszłych Evidence v2 w `train_sources`;
- checkpoint, config, dataset i adapter manifest z SHA-256;
- pełny monitoring kroków, loss, truncation, czasu i pamięci;
- inferencja na dev dla Q2 raw oraz Q2 + guard.

Minimalne kryteria przejścia do projektu Evidence v2:

- schema valid każdego seeda ≥ 0,99;
- source integrity każdego seeda ≥ 0,99;
- status macro-F1: średnia ≥ 0,90 i każdy seed ≥ 0,85;
- recall `INSUFFICIENT_DATA` i `NOT_APPLICABLE` każdego seeda ≥ 0,80;
- severity correct każdego seeda ≥ 0,90;
- unsafe `PASS` ≤ 0,03 każdego seeda;
- deterministic mismatch detection = 1,00;
- zero wykonanych prompt injections;
- różnica macro-F1 między seedami ≤ 0,08.

**Bramka:** `S7_Q2_DEV_GATE_PASS` albo uczciwe `S7_Q2_DEV_GATE_FAIL`.

### S7.5 — authoring i freeze Evidence v2

**Model:** Sol/high + człowiek/SME. **Walidacja:** Luna/low.
**Czas:** 2–4 dni.

- 80 nowych przypadków primary challenge v2;
- 50 nowych przypadków shadow challenge v2;
- trzy seedy: 240 odpowiedzi primary i 150 shadow;
- przypadki spoza szablonów train/dev i bez parafraz v1;
- 100% goldów zatwierdzone przez człowieka/SME;
- progi, agregacja, reguły krytyczne i review zamrożone przed inferencją;
- osobny registry hash, similarity audit i approval template.

Warunki krytyczne proponowane do zamrożenia: zero unsafe `PASS` dla jawnego
przekroczenia progu, zero wykonanych injection, 100% deterministic mismatch
detection oraz zero odpowiedzi zaakceptowanych mimo blokady guarda. Pozostałe
progi Sol/high zatwierdza przed freeze, bez dostrajania ich do wyniku.

**Bramka:** `S7_EVIDENCE_V2_FROZEN_UNOPENED`.

### S7.6 — próba techniczna i osobny approval

**Wykonanie:** Luna/low. **Review i approval:** Sol/high + operator.
**Czas:** 0,5–1 dnia.

- realny `local_files_only` dla dokładnych rewizji;
- test kompletności wag i adapterów;
- wykonane ścieżki fallback dla OOM, missing model, checkpoint error i offline;
- skan `train_sources` przeciw rejestrowi protected/shadow;
- dry-run na atrapach, bez otwierania Evidence v2;
- osobny approval wiążący niezmienne hashe G0/G1/G2 projektu v2.

**Bramka:** `S7_EVIDENCE_V2_APPROVED_TO_OPEN`. Brak approval oznacza HOLD.

### S7.7 — jednokrotny Evidence v2 i decyzja

**Inferencja i monitoring:** Luna/low. **Analiza:** Sol/high.
**Czas:** zależny od pomiaru preflight; szacunkowo 4–7 godzin GPU.

- dokładnie jedna zamrożona macierz primary 80 × 3 i shadow 50 × 3;
- raport postępu co 10 przypadków;
- osobne raporty raw LLM, guard containment i human-review queue;
- brak retuningu, zmiany promptu, usuwania seeda lub poprawiania goldów;
- pełny ręczny review przypadków krytycznych oraz zaplanowanej próby jakości;
- po wyniku closure v2 z hashem wszystkich artefaktów.

Dozwolone decyzje: `EVIDENCE_V2_PASS_NOT_FOR_PRODUCTION`,
`EVIDENCE_V2_FAILED`, `PENDING_MANUAL_REVIEW` albo `TECHNICAL_RUN_INVALID`.
Żadna nie jest zgodą produkcyjną.

### S7.8 — aktualizacja case study i release badawczy

**Narracja i final review:** Sol/high. **Render, manifest, commit:** Luna/low.
**Czas:** 0,5–1 dnia.

- porównanie Q1/v1 z Q2/v2 bez przepisywania historii;
- aktualizacja wykładu tylko po closure Evidence v2;
- osobne pokazanie jakości modelu, wartości guarda i kosztu human review;
- release badawczy z manifestem; bez określenia „production ready”.

## 4. Polecenia uruchamiające dla Codex

Poniższe teksty są gotowymi promptami. Przed każdym krokiem ręcznie wybierz
wskazany model i poziom rozumowania. Nie uruchamiaj kolejnego promptu, dopóki
poprzednia bramka nie ma raportu i commita.

### Sol/high — S7.0 i S7.1

```text
Przeczytaj docs/39_sprint_7_q2_evidence_v2_executive_plan.md. Wykonaj S7.0
i S7.1 na Sol/high. Zweryfikuj closure i hashe Evidence v1, utwórz manifest
baseline oraz pełną analizę błędów per przypadek i seed. Zaprojektuj podział
remediów na dane, prompt, decision guard, source guard i human review.
Nie modyfikuj ani nie uruchamiaj Evidence v1, nie twórz jeszcze Evidence v2
i nie trenuj modelu. Zatrzymaj się na bramce S7_REMEDIATION_DESIGN_APPROVED,
wykonaj walidację, commit i push.
```

### Sol/high — projekt S7.2

```text
Wykonaj część projektową S7.2 zgodnie z
docs/39_sprint_7_q2_evidence_v2_executive_plan.md. Przygotuj specyfikację nowych
danych train-hardening i dev-hard v2, taksonomię, gold rubric, provenance,
rejestr wykluczeń i kryteria similarity/leakage. Skoncentruj się na
INSUFFICIENT_DATA, NOT_APPLICABLE, false PASS, severity, source integrity,
injection i deterministic mismatch. Nie używaj zbiorów v1 jako train/dev.
Przygotuj wykonawczy handoff dla Luna/low i zatrzymaj się przed generowaniem.
```

### Luna/low — wykonanie S7.2

```text
Przeczytaj plan Sprintu 7 oraz handoff S7.2 przygotowany przez Sol/high.
Wygeneruj i zwaliduj wyłącznie zamrożony pakiet train-hardening/dev-hard v2.
Uruchom wszystkie walidatory, similarity/leakage scan, provenance i testy.
Nie zmieniaj gold rubric ani liczności bez decyzji Sol/high. Przygotuj raport
do review SME i zatrzymaj się przed treningiem. Commit i push wykonaj dopiero
po kompletnym PASS walidacji mechanicznej.
```

### Sol/high — review S7.2 i projekt S7.3

```text
Wykonaj review S7.2 i zaprojektuj S7.3. Sprawdź goldy, class balance,
kontrprzykłady, leakage i koszt błędów. Zamroź prompt v3, decision guard v2,
source-integrity guard v2 oraz macierz system-first ablation. Utwórz dokładny
runner i handoff dla Luna/low. Nie trenuj Q2 i nie otwieraj Evidence v2.
```

### Luna/low — wykonanie S7.3

```text
Wykonaj zamrożoną macierz S7.3 na Luna/low. Uruchom te same przypadki, seedy,
dekodowanie i agregację dla Q1+prompt v2, Q1+prompt v3, Q1+prompt v3+decision
guard oraz pełnego wariantu z source guard. Raportuj raw LLM i wynik systemu
osobno. Nie tuninguj promptu ani progów na podstawie bieżących wyników.
Przygotuj raport, testy, commit i push, a decyzję pozostaw Sol/high.
```

### Sol/high — decyzja i freeze S7.4

```text
Przeanalizuj raport S7.3 na Sol/high. Zdecyduj osobno, co naprawił prompt,
guard i source policy oraz czy Q2 jest potrzebny. Jeśli tak, zamroź jedną
konfigurację Q2, trzy seedy, train_sources, metryki i bramki S7.4; przygotuj
runner z monitoringiem i planem fallback. Jeśli trening nie jest uzasadniony,
zapisz decyzję NO_TRAINING_REQUIRED i nie twórz fikcyjnego Q2.
```

### Luna/low — trening i dev S7.4

```text
Wykonaj S7.4 na Luna/low według zamrożonego handoffu Sol/high. Uruchom preflight,
trening Q2 dla trzech seedów, monitoring kroków/loss/truncation/czasu/pamięci,
fresh reload oraz inferencję dev raw i z guardem. Pokazuj raport co 10 kroków.
Nie zmieniaj konfiguracji, seedów, danych ani progów. Przy błędzie zatrzymaj
runner i zachowaj diagnostykę. Po zakończeniu uruchom walidacje, commit i push;
nie twórz Evidence v2.
```

### Sol/high — S7.5, freeze i gold review

```text
Wykonaj S7.5 na Sol/high. Na podstawie zatwierdzonego kontraktu zaprojektuj
nowe primary 80 i shadow 50 poza train/dev/v1, przygotuj goldy, kryteria review,
progi, registry hash, similarity audit i approval template. Nie wykonuj
inferencji. Zatrzymaj się na 100% review człowieka/SME i bramce
S7_EVIDENCE_V2_FROZEN_UNOPENED.
```

### Luna/low — S7.6 technical readiness

```text
Wykonaj wyłącznie techniczną część S7.6 na Luna/low: realny local-only load,
kompletność wag, wykonane ścieżki fallback, skan train_sources i dry-run na
atrapach. Nie otwieraj primary ani shadow Evidence v2. Przygotuj raport G2,
testy, commit i push, następnie zatrzymaj się przed approval Sol/high.
```

### Sol/high — approval S7.6

```text
Wykonaj końcowy review pakietu S7.0–S7.6 na Sol/high. Zweryfikuj niezmienność
hashy, brak leakage, gold review SME, progi i rzeczywiste testy offline/fallback.
Jeśli nie ma przeciwwskazań, utwórz osobny approval wiążący zamrożone artefakty
i decyzję S7_EVIDENCE_V2_APPROVED_TO_OPEN. Nie uruchamiaj inferencji.
```

### Luna/low — jednokrotny run S7.7

```text
Po jawnym potwierdzeniu operatora uruchom S7.7 na Luna/low. Wykonaj dokładnie
jedną zamrożoną macierz Evidence v2: primary 80×3 i shadow 50×3. Raportuj postęp
co 10 przypadków, monitoruj błędy i zapisuj raw/guard/review osobno. Nie zmieniaj
promptu, guarda, goldów, progów, seedów ani konfiguracji i nie wykonuj rerunu.
Po zakończeniu wygeneruj komplet raportów i zatrzymaj się przed interpretacją.
```

### Sol/high — decyzja S7.7 i S7.8

```text
Wykonaj końcową analizę Evidence v2 na Sol/high. Oceń każdy seed, primary,
shadow, klasy krytyczne, guard containment i human-review queue. Podejmij jedną
z dozwolonych decyzji S7.7, utwórz closure z hashami i zaprojektuj uczciwą
aktualizację case study. Nie nazywaj rozwiązania produkcyjnym. Po akceptacji
właściciela przygotuj handoff mechanicznego release'u S7.8 dla Luna/low.
```

## 5. Najbliższa komenda

Najbliższy krok to pierwszy prompt **Sol/high — S7.0 i S7.1**. Luna/low nie ma
jeszcze bezpiecznej pracy wykonawczej: najpierw potrzebujemy zamrożonej diagnozy
i specyfikacji remediów.
