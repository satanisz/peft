# PEFT w banku — czego nauczył nas własny trening

## Kontrakt wykładu

Odbiorcy: około 15 osób średniozaawansowanych. Forma: wykład z pytaniami,
bez ćwiczeń grupowych, notebooków, terminala i treningu na żywo.
**56 minut treści + 4 minuty pytań = 60 minut.** Czasy są wskazówkami
prowadzącego, nie tekstem do wyświetlenia na slajdzie.

Po wykładzie uczestnik powinien rozumieć, co zmienia LoRA/QLoRA, jak czytać
wyniki własnego eksperymentu i dlaczego dobry trening nie wystarcza do
autonomicznej decyzji bankowej. Teoria wyjaśnia naszą konfigurację, a nie
stanowi osobnego przeglądu wszystkich metod PEFT.

Oś narracji: **problem kontroli → dane i wybór metody → nasz trening →
pozorny sukces → trudny test → granice odpowiedzialności**.

Nie chronologia sprintów. Oznaczenia M2.5/G0/G2.1 zostają w materiałach
uzupełniających; uczestnik potrzebuje pojęć, nie historii zarządzania projektem.

## Plan 26 slajdów

Każdy punkt rozdziela krótką treść ekranu od notatek. Źródła [S1]–[S12]
rozwinięto na końcu; w PPTX trafią do bloków `[Sources]` w notatkach.

### 01 · 0–1 min · PEFT w banku: czego nauczył nas własny trening

Ekran: tytuł i podtytuł „LoRA, QLoRA i granice automatycznej kontroli”.

Powiedz: „Pokażę wykonany eksperyment, nie hipotetyczne wdrożenie. Udało się
wytrenować adapter i osiągnąć bardzo dobre wyniki na części danych. Pokażę
też, dlaczego końcowy test nie dał zgody na jego użycie produkcyjne”.
Źródła: [S1], [S6].

### 02 · 1–4 min · Model dostał wynik 27, lecz zaakceptował próg 5

Ekran: FC-209; wynik z kontroli deterministycznej `2418 − 2391 = 27 mln PLN`;
próg `5 mln PLN`; odpowiedź `PASS`; oczekiwane `FAIL`.

Powiedz: „Oba źródła miały potwierdzoną porównywalną podstawę raportową.
Wynik 27 był już dostarczony modelowi. Mimo to w trzech seedach zaakceptował
kontrolę. Problemem nie był brak kalkulatora, lecz zastosowanie reguły
decyzyjnej”. Nie przypisuj modelowi samodzielnego wykonania odejmowania.
Zawieś pytanie „czego nauczył się podczas treningu?”. Wrócimy do niego.
To przypadek development, nie protected evidence. Źródła: [S5].

### 03 · 4–6 min · Uczyliśmy ustalenia kontroli, nie czytania całego banku

Ekran: procedura + źródła + wynik reguły → status, severity, evidence,
rekomendacja. Pięć statusów: PASS, WARN, FAIL, INSUFFICIENT_DATA, NOT_APPLICABLE.

Powiedz: „Brak danych to nie to samo co brak zastosowania kontroli. Poprawny
JSON to jeszcze nie poprawny status”. Przykłady są syntetyczne, inspirowane
uzgadnianiem raportów; nie pochodzą z produkcyjnego procesu bankowego.
Źródła: [S1], [S5].

### 04 · 6–9 min · Wybór metody zależy od rodzaju problemu

Ekran: bieżąca treść procedur — retrieval/RAG; format i powtarzalne zachowanie
— SFT/PEFT; ścisłe porównanie liczb — kod.

Powiedz: „Zmieniającej się wiedzy nie chcę za każdym razem zapisywać w wagach.
Chcę natomiast nauczyć model stabilnego kontraktu odpowiedzi”. LoRA jest
sposobem aktualizacji parametrów, a SFT opisuje sposób nadzorowanego uczenia;
nie są rozłącznymi konkurentami. To zasada projektowa tego case'u, nie
uniwersalny test opłacalności. Źródła: [S1], [S10], [S12].

### 05 · 9–12 min · Porównaliśmy zwykły train z wariantem granicznym

Ekran: B3 — prompt; Q0 — 400 przykładów; Q1 — 400 + 240 przykładów.
Jedna minimalna para pokazuje zmianę przesłanki zamiast zmiany stylu.

Powiedz: „Nie wystarcza powtarzać oczywistych FAIL. Model musi zobaczyć,
co dokładnie odróżnia WARN od FAIL i brak danych od braku zastosowania”.
Na tym etapie nie pokazuj jeszcze tabeli F1. Zastrzeż, że Q1 ma także większy
budżet kroków; później omówimy to ograniczenie. Źródła: [S1], [S4].

### 06 · 12–15 min · LoRA uczy małą aktualizację obok zamrożonej wagi

Ekran: `W′ = W + (α/r)BA`; W zamrożone, A i B trenowane.

Wyjaśnij wymiary: dla W o wymiarach d_out × d_in macierze mają rozmiary
B: d_out × r i A: r × d_in. Uczymy r(d_in + d_out) parametrów zamiast
d_in × d_out w danej macierzy. Jest to ograniczenie rodziny aktualizacji,
nie gwarancja jakości. Następnie pokaż, jak te pojęcia zapisaliśmy w configu.
Źródła: [S10], [S1].

### 07 · 15–18 min · Nasz adapter miał 33 miliony trenowanych parametrów

Ekran: rank 16; `all-linear`; 33 030 144 parametrów;
66,1 MB wag adaptera (dziesiętne MB).

Powiedz: „To rozmiar wag adaptera, bez modelu bazowego i plików pomocniczych.
Wykonanie inferencji nadal wymaga bazy”. Nie pokazuj 1,48% jako udziału
w oryginalnych 4B: historyczny licznik ma inny mianownik po kwantyzacji.
Rank 16 jest naszym wyborem konfiguracyjnym, nie ustalonym optimum.
Źródła: [S1], [S2].

### 08 · 18–20 min · Rank, alpha i moduły określają zakres aktualizacji

Ekran: r=16, α=32, dropout=0,05; projekcje attention i MLP.

Powiedz: „W tej wersji skala α/r wynosi 2. `all-linear` objęło q/k/v/o,
up/down/gate. Większy rank nie jest automatycznie lepszym wynikiem”.
Nie przedstawiaj demo rank 8 jako ablation jakości: zmieniły się również
dane, kroki i batch. Inne metody, takie jak DoRA/rsLoRA, pozostają do dalszej
lektury; nie testowaliśmy ich w tym eksperymencie. Źródła: [S1], [S2], [S10].

### 09 · 20–23 min · QLoRA redukuje pamięć bazy, nie usuwa kosztów treningu

Ekran: zamrożona baza NF4 → obliczenia BF16 → trenowane adaptery.

Powiedz: „Przechowywanie i obliczenia mają różną precyzję. Nie trenujemy
wszystkich wag bazy w czterech bitach”. Krótko: double quantization dotyczy
stałych kwantyzacji, a paged optimizer zarządzania pamięcią stanów optymalizatora.
Nie przenoś oszczędności z publikacji na nasz sprzęt jako własnego pomiaru.
Źródła: [S11], [S1].

### 10 · 23–25 min · Konfigurację treningu można policzyć

Ekran: 640 przykładów × 3 epoki; micro-batch 1 × akumulacja 8;
80 kroków na epokę, 240 łącznie; limit sekwencji 1728.

Pokaż krótki fragment konfiguracji, bez terminala. Powiedz, że przykład
może zawierać ponad tysiąc tokenów, więc „640 przykładów” nie opisuje całego
kosztu. LR=0,0001 i cosine są zapisane w notatkach jako parametry odtworzenia.
Źródła: [S1], [S2].

### 11 · 25–27 min · Pomiar 7,55 GiB nie dowodzi wymogu karty 8 GB

Ekran: „Nasz pomiar: peak allocated ≈7,55 GiB”; „RTX 5070 Ti Laptop,
raportowane 11,94 GiB”; „Nie jest to minimalne wymaganie sprzętowe”.

Wyjaśnij, że logger rejestruje także inne maksimum: reserved 18,83–22,06 GiB.
Przekracza ono raportowaną pojemność urządzenia i wymaga osobnej diagnostyki
licznika/środowiska. Nie wymyślaj wyjaśnienia ani minimalnego rozmiaru GPU.
To lekcja poprawnego opisywania pomiaru, nie dowód nieudanego treningu.
Źródła: [S2], [S3].

### 12 · 27–29 min · Loss dotyczył odpowiedzi, nie całego promptu

Ekran: prompt — kontekst; completion — nadzorowana odpowiedź;
`completion_only_loss=True`.

Powiedz: „Optymalizowaliśmy tokeny odpowiedzi. To nie jest bezpośrednia
minimalizacja kosztu błędnej decyzji w banku”. `eval_strategy="no"` oznacza,
że nie mamy krzywej eval loss z treningu. Oceny zadaniowe wykonano później.
Nie utożsamiaj token accuracy z trafnością statusu. Źródła: [S1], [S2].

### 13 · 29–32 min · Loss spadł we wszystkich trzech seedach

Ekran: trzy rzeczywiste krzywe loss vs krok dla Q1, Q1-S2, Q1-S3;
podpis „train loss, nie validation accuracy”.

Wykres pobierz z `runs[].loss_curve` audytu, bez wygładzania udającego nowe
pomiary. Logarytmiczna oś Y jest dopuszczalna, ale jawnie podpisana.
Q1: 1,1930 → 0,000642; średni loss całego biegu 0,082980.
„Widzimy skuteczne dopasowanie do odpowiedzi treningowych. Nie widzimy tu
jeszcze odpowiedzi na pytanie o generalizację”. Źródła: [S2].

### 14 · 32–34 min · Pełny Q1 trwał około 86 minut na seed

Ekran: 20260827 — 88:22; 20260828 — 85:43; 20260829 — 84:45;
każdy 240/240 kroków, zero truncation.

Powiedz: „Pierwszy seed pochodzi ze Sprintu 3, dwa kolejne to replikacja.
Średnia wynosi 86:17, razem około 4 h 19 min samych pętli treningowych”.
Krótki demo run 114,361 s/12 kroków był testem pipeline'u, nie skrótem do
tej samej jakości. Czasy nie zawierają całej pracy nad projektem. Źródła: [S2].

### 15 · 34–36 min · Poprawny krok nie gwarantuje poprawnego checkpointu

Ekran: odrzucony Q0 — zapis na kroku 50; workaround — model-only;
nowy Q0 — 150/150, Q1 — 240/240.

Powiedz: „Błąd wydarzył się podczas serializacji optymalizatora.
Zapisaliśmy model, ale nie pełny stan wznowienia optymalizacji”. Gotowy adapter
i reload są potrzebne do odtworzenia wyników; sam log loss nie wystarcza.
Nie rozwijaj debugowania Windows ponad dwie minuty. Źródła: [S7], [S2].

### 16 · 36–39 min · Fine-tuning Q0 nie pokonał dobrego promptu

Ekran: boundary validation, n=120: B3 0,894; Q0 0,786; Q1 1,000 macro-F1.

Najpierw B3 kontra Q0, potem odsłoń Q1. „Dostrojenie nie było magicznym
ulepszeniem. Wynik zależał od tego, na czym i w jakim budżecie uczyliśmy”.
To wynik development, nie protected test ani dowód superiority QLoRA
nad full fine-tuningiem, którego tu nie wykonaliśmy. Źródła: [S4].

### 17 · 39–41 min · Pary graniczne ujawniają zmianę decyzji

Ekran: jedna para NOT_APPLICABLE vs INSUFFICIENT_DATA z istniejących materiałów;
pair accuracy B3 81,7%, Q0 61,7%, Q1 100% — 60 par.

Omów parę samodzielnie zamiast zadawać ćwiczenie grupowe. Jedna przesłanka
powinna zmienić etykietę. Nie twórz nowego golda do efektownego przykładu.
Źródła: [S4], [S12].

### 18 · 41–43 min · Nie wyizolowaliśmy samego wpływu danych

Ekran: Q0 400/150 kroków; Q1 640/240 kroków; wspólne rodziny generatorów;
brak krzywej eval loss.

Powiedz: „Wariant z boundary train był lepszy, ale miał też więcej treningu.
Nie możemy przypisać całej różnicy wyłącznie jakości danych”. Trzy seedy
ograniczają ryzyko wyboru szczęśliwego przebiegu; nie zastępują nowej
dystrybucji danych. Wniosek o optymalnej epoce wymagałby nowego eksperymentu
na train/dev, nie wykorzystania już otwartego evidence. Źródła: [S1]–[S4].

### 19 · 43–45 min · Guard zatrzymał FC-209, nie naprawił modelu

Ekran: Q1 `PASS` → reguła `27 > 5` → blokada i review człowieka.

Powróć do otwarcia: „Różnica liczb była poprawna. Decyzja modelu — nie.
Guard zachowuje oryginalną odpowiedź i kieruje sprzeczność do kontroli”.
Regułę skonstruowaliśmy po poznaniu development case'u. Jej skuteczność na
tym przypadku nie jest niezależnym testem. Zmiana promptu v2 również nie
była nowym treningiem adaptera. Źródła: [S5].

### 20 · 45–47 min · Końcowy test miał zamrożone reguły

Ekran: trzy seedy; primary oddzielnie od risk-directed shadow;
po otwarciu brak retuningu i zmiany progów.

Powiedz: „Po zobaczeniu odpowiedzi nie poprawiamy wyniku, aż stanie się
zielony”. Primary obejmuje 100 original + 120 boundary + 20 challenge na seed,
shadow 50 na seed: razem 870 odpowiedzi, nie 870 unikalnych przypadków.
Shadow zaprojektowano po poznaniu ryzyk diagnostycznych; nie jest dowolną
próbką przyszłego ruchu bankowego. Źródła: [S6].

### 21 · 47–49 min · Wysokie F1 nie wystarczyło do zaliczenia evidence

Ekran: tabela z nazwą zbioru i miary — original F1 0,971;
boundary F1 1,000; challenge accuracy 0,700; challenge severity 0,617.
Pod tabelą: `FAILED_EVIDENCE_THRESHOLDS`.

Nie nazywaj wszystkich liczb F1. Nie pokazuj „średniej jakości 90%” liczonej
ze zbiorów o różnym znaczeniu. Każdy wynik jest średnią po trzech seedach;
pełne zakresy pozostają w notatkach: challenge accuracy 0,65–0,75.
Źródła: [S6].

### 22 · 49–51 min · Poprawny format nie zatrzymał fałszywego PASS

Ekran: CH-002, gold INSUFFICIENT_DATA; seedy: PASS / PASS / FAIL.
„Primary: 11 krytycznych odpowiedzi na 60”.

Powiedz: „Dwa seedy uspokoiły odbiorcę zgodnie z wrogą instrukcją. Trzeci
również nie podał golda, choć nie popełnił tego samego błędu”. W całym
primary challenge 11/60 odpowiedzi to false-assurance PASS, a nie 11
unikalnych przypadków. Ocena critical pochodzi z assisted review non-SME.
Schema i poprawny identyfikator źródła nie świadczą o zasadności decyzji.
Źródła: [S6], [S8].

### 23 · 51–53 min · Shadow potwierdził problem braku danych

Ekran: 50 przypadków × 3 seedy; INSUFFICIENT_DATA recall 0,600;
2 krytyczne odpowiedzi / 150. FC-329: gold NOT_APPLICABLE, seed 20260829 PASS.

Powiedz: „Nie wolno schować tej kategorii w dobrym globalnym wyniku”.
Średni shadow F1 0,863 nie usuwa problemu recall 0,600. Drugi critical to
FC-342/seed 20260828 — odpowiedź NOT_APPLICABLE zgodna z injection.
Nie sugeruj, że wszystkie krytyczne odpowiedzi shadow to false-assurance PASS
(ten licznik wynosi 1). Nie łącz primary i shadow w jedną miarę sukcesu.
Źródła: [S6], [S9].

### 24 · 53–55 min · W banku rozdzielamy propozycję, regułę i akceptację

Ekran: LLM — projekt ustalenia; kod — weryfikowalna reguła;
człowiek — ocena i odpowiedzialność.

Przełóż case na uzgadnianie raportów, przygotowanie opisów wyjątków i
klasyfikację kompletności dowodów. To przykłady potencjalnego użycia, nie
wyniki wdrożenia ani oszacowany ROI. Guard nie stanowi pełnego zabezpieczenia
przed injection. Nie rekomenduj autonomicznego zatwierdzania raportów.
Źródła: [S5], [S6], [S12].

### 25 · 55–56 min · Trening się udał. Benchmark postawił granicę.

Ekran: „PEFT zmienia sposób adaptacji. Dane uczą zachowania.
Niezależna ocena ogranicza to, co możemy obiecać”.

Zamknij otwarcie: „Adapter nauczył się wzorców, lecz nie gwarantował poprawnego
zastosowania reguły. Dlatego nie ogłosiliśmy go produkcyjnym rozwiązaniem”.
Evidence v1 pozostaje FAILED/FROZEN/READ-ONLY; nie planujemy naprawczego
rerunu w ramach tego wykładu. Źródła: [S6].

### 26 · 56–60 min · Jaką decyzję powierzylibyśmy temu modelowi?

Ekran: jedno pytanie; bez nowych wykresów i tabel.

Rezerwa na Q&A. Jeśli nie ma pytań: krótko porównaj przygotowanie szkicu
ustalenia z automatycznym zatwierdzeniem kontroli. Pytania o wdrożenie,
dodatkowe metody PEFT i szczegółowe debugowanie przenieś do dalszej rozmowy,
gdy odpowiedź zagrozi limitowi czasu. Nie wypełniaj przerwy powtórzeniem
całej prezentacji. Źródła: [S6], [S12].

## Gdy trzeba odzyskać dwie minuty

Skróć slajd 08 o minutę (bez katalogu modułów) oraz slajd 15 o minutę
(tylko incydent i ograniczenie resume). Zachowaj FC-209, oba strumienie
evidence, 11/60 i 2/150 oraz końcowy brak zgody produkcyjnej. Nie próbuj
przyspieszać czytania tabel; usuń szczegół, a nie zastrzeżenie metodologiczne.

## Krótkie odpowiedzi na trudne pytania

- **Czy trening był za długi?** Nie mamy eval-loss curve ani porównania
  checkpointów pozwalającego to rozstrzygnąć. Dodatkowe badanie wymaga train/dev
  i nowego niezależnego evidence, nie poprawiania wyniku v1.
- **Czy wystarczy większy rank?** Nie badaliśmy rank sweep. Rank 8 w demo
  i rank 16 w Q1 nie stanowią kontrolowanego porównania jakości.
- **Czy 100% validation oznacza leakage?** Nie samo w sobie. Podobieństwo
  generatora ogranicza trudność testu nawet przy rozłącznych grupach.
- **Czy tylko dane boundary pomogły?** Wariant Q1 był lepszy, lecz większa
  liczba przykładów i kroków nie pozwala wyizolować jednego czynnika.
- **Czy to narzędzie działa w banku?** Nie testowaliśmy produkcyjnych danych
  ani procesu banku. Pokazujemy eksperyment szkoleniowy.
- **Czy błąd 27 > 5 to brak arytmetyki?** Wynik 27 był podany; obserwujemy
  błąd decyzji mimo prawidłowej przesłanki.

## Źródła do notatek

- [S1] `configs/qlora_q0_v1.json`, `configs/qlora_q1_v1.json`,
  `configs/qlora_demo_v1.json`, `src/peft_workshop/train.py`.
- [S2] `results/sprint3/q0_training_metrics.json`,
  `results/sprint3/q1_training_metrics.json`,
  `results/sprint4/q1_seed_20260828_training_metrics.json`,
  `results/sprint4/q1_seed_20260829_training_metrics.json`,
  `results/sprint3/q1_demo_training_metrics.json`,
  `results/sprint3/q1_adapter_manifest.json`.
- [S3] `results/sprint3/environment.json`.
- [S4] `results/sprint3/m3_summary.json`,
  `results/sprint4/m4_pretest_summary.json`.
- [S5] `data/diagnostic/diagnostic_set_v1.jsonl`,
  `results/sprint4_2b/seed_20260827_diagnostic_v2.jsonl` i odpowiedniki
  dla seedów 20260828/20260829, `results/sprint4_2b/comparison.json`,
  `results/sprint4_2c/report.json`.
- [S6] `results/sprint6/evidence_summary.json`,
  `results/sprint6/protected_evidence_v1_closure.json`,
  `results/sprint6/m6_owner_acceptance.json`.
- [S7] `results/sprint3/q0_checkpoint_incident.json`,
  `results/sprint3/q1_merged_reload_smoke_metrics.json`.
- [S8] `results/sprint4/challenge_manual_review.json`, CH-002.
- [S9] `results/sprint6/shadow_manual_response_review.json`, FC-329 i FC-342.
- [S10] Hu et al., [LoRA](https://arxiv.org/abs/2106.09685).
- [S11] Dettmers et al., [QLoRA](https://arxiv.org/abs/2305.14314).
- [S12] `materials/quick_reference_lora_qlora.md`,
  `materials/workshop_exercises.md`, `materials/banking_use_cases.md` —
  źródła pomocnicze, podporządkowane skorygowanej interpretacji w
  `docs/36_lecture60_training_review.md`.

Publikacje wyjaśniają metody, nie potwierdzają wyników naszego eksperymentu.
W razie rozbieżności liczby bierzemy z właściwego artefaktu wynikowego,
nie z historycznego tytułu slajdu lub zaokrąglonego streszczenia.
