# Review treningu — podstawa wykładu PEFT 60 minut

## Wniosek

**Trening zakończył się technicznie poprawnie. Model nauczył się syntetycznego
kontraktu zadania, lecz nie przeszedł końcowego benchmarku bezpieczeństwa.**
Wykład powinien pokazać wszystkie trzy części tego zdania.

To nowy, odczytowy przegląd istniejących wyników, nie kolejny trening ani
evidence run. Liczby i hashe źródeł odtwarza
`scripts/audit_lecture_training.py`; wynik:
`results/lecture60/training_audit.json`.

## 1. Co faktycznie wytrenowaliśmy

Model bazowy: `Qwen/Qwen3-4B-Instruct-2507`, rewizja
`cdbee75f17c01a7cc42f958dc650907174af0554`.
Środowisko referencyjne: Windows 11, RTX 5070 Ti Laptop GPU,
raportowana pamięć urządzenia 11,94 GiB. To nie jest benchmark wielu GPU.

Q0: 400 rekordów standardowego train. Q1: te same 400 plus 240 rekordów
granicznych; łącznie 640 syntetycznych przykładów i 200 grup. Nie są to
poufne dokumenty banku ani trening na całych rzeczywistych sprawozdaniach.
Zadaniem jest utworzenie ustrukturyzowanego ustalenia kontroli na podstawie
procedury, źródeł i dostępnych wyników kontroli deterministycznych.

Q0/Q1: NF4 + double quantization, BF16 compute, rank 16, alpha 32,
dropout 0,05, `all-linear`, learning rate 0,0001, scheduler cosine,
micro-batch 1, akumulacja 8, trzy epoki, limit 1728 tokenów,
gradient checkpointing i completion-only loss. Brak packing.

| Bieg | Seed | Przykłady | Kroki | Czas pętli treningowej | Średni train loss | Ostatni logowany loss | Peak allocated GiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q0 | 20260827 | 400 | 150/150 | 54 min 53 s | 0,118611 | 0,001430 | 7,384 |
| Q1 | 20260827 | 640 | 240/240 | 88 min 22 s | 0,082980 | 0,000642 | 7,551 |
| Q1-S2 | 20260828 | 640 | 240/240 | 85 min 43 s | 0,078937 | 0,000881 | 7,552 |
| Q1-S3 | 20260829 | 640 | 240/240 | 84 min 45 s | 0,080171 | 0,000387 | 7,551 |
| Q1-DEMO | 20260827 | 50 | 12/12 | 114,361 s | 0,799904 | 0,456720 | 7,487 |

Q1-DEMO używa rank 8 i akumulacji 4; nie jest pełnym Q1 ani kontrolowanym
porównaniem jakości rank 8 vs 16. Q1 z pierwszego seeda pochodzi ze Sprintu 3,
dwa kolejne biegi ze Sprintu 4 — to łącznie trzy, a nie cztery seedy Q1.
Ich pętle treningowe trwały razem 4 h 18 min 50 s, średnio 86 min 17 s.
Nie obejmuje to przygotowania danych, pobierania i ładowania modelu,
końcowego eksportu, inferencji, review ani odrzuconego biegu Q0.

## 2. Czy trening przebiegał prawidłowo

W pięciu sprawdzonych artefaktach: `completed`, oczekiwana liczba kroków,
zero truncation, rosnące numery logowanych kroków oraz skończone wartości
loss/gradient norm/learning rate. Hashe konfiguracji, źródeł treningowych
i lokalnych końcowych wag adapterów zgadzają się. Nie ma wskazania, że
zaakceptowane Q1 są niedokończone. To nie dowodzi braku dowolnej przerwy
systemowej między zapisami logów.

Loss Q1 spada w podobny sposób we wszystkich seedach. Przykładowo pierwszy
seed: 1,1930 na kroku 1; 0,03120 na kroku 80; 0,001176 na kroku 160;
0,000642 na kroku 240. Ostatni loss nie jest średnim `train_loss=0,082980`.
Krzywe należy rysować z `log_history`, nie interpolować z jednego punktu.

Nie ma krzywej `eval_loss` (`eval_strategy="no"`). Nie można zatem stwierdzić,
że nie wystąpił overfitting, wybrać optymalnej epoki ani dowieść, że dłuższy
trening rozwiązałby późniejsze błędy. Niemal zerowy loss i wysoka token accuracy
opisują przewidywanie tokenów odpowiedzi treningowych, nie bezpieczeństwo
decyzji. Dobre wyniki na podobnym generatorze i słabsze na trudniejszych
przypadkach są zgodne z ograniczoną generalizacją; nie rozstrzygają jej jednej
przyczyny.

Pierwszy Q0 zawiesił się przy zapisie stanu optymalizatora na kroku 50/150.
Ten bieg odrzucono. Udokumentowany workaround `save_only_model=true` pozwolił
ukończyć nowy Q0 oraz Q1. Koszt: checkpoint nie zapewnia pełnego odtworzenia
stanu optymalizatora. Nie przedstawiać tego jako bezproblemowego resume.
Źródło: `results/sprint3/q0_checkpoint_incident.json`.

## 3. Co poprawiło się na development

Na tym samym boundary validation (120 przypadków, 60 par):

| Wariant | Status macro-F1 | Pair accuracy |
|---|---:|---:|
| B3 — baseline promptowy | 0,894 | 81,7% |
| Q0 — standardowy train | 0,786 | 61,7% |
| Q1 — standardowy + boundary train | 1,000 | 100% |

Źródło: `results/sprint3/m3_summary.json`, `comparison`.
Wniosek: samo wykonanie fine-tuningu nie gwarantuje poprawy nad dobrym promptem;
wariant z danymi granicznymi osiągnął lepszy wynik rozwojowy. **Nie jest to
czysta ablacja efektu jakości danych**: Q1 ma także więcej przykładów i kroków
(240 vs 150), inny warmup (12 vs 8) i rytm checkpointów. Nie wykonano wariantu
kontrolnego z równym budżetem obliczeń. Dawne sformułowanie „izoluje wartość
danych” należy złagodzić w nowym wykładzie.

Trzy Q1 mają status macro-F1 1,000 na original i boundary validation, lecz
severity original wynosi 94%, 94%, 98%. W jednym seedzie wystąpił błędny
`source_id` BD-0360. Dodatkowo dawne etykiety severity nie są w pełni spójne
z późniejszą polityką; original severity jest legacy/report-only.
Nie łączymy tych metryk z późniejszą walidacją severity policy-v1.

Redukcja średniego wejścia względem B3 wynosi 51,6% (2896,9167 do 1400,9167
tokena na boundary validation). To nie oznacza automatycznie 51,6% niższego
kosztu ani takiego samego przyspieszenia. To porównanie konfiguracji systemów,
nie wyizolowanego wpływu samych wag adaptera.

## 4. Co wiemy z końcowego evidence

| Obszar | Miara | Wynik |
|---|---|---:|
| Original test | średni status macro-F1, 3 seedy | 0,971 |
| Boundary test | średni status macro-F1, 3 seedy | 1,000 |
| Primary challenge | średnia status accuracy | 0,700 |
| Primary challenge | średnia poprawność severity | 0,617 |
| Primary challenge | krytyczne odpowiedzi / wszystkie odpowiedzi | 11/60 |
| Shadow | średni macro-F1 | 0,863 |
| Shadow | średni recall INSUFFICIENT_DATA | 0,600 |
| Shadow | krytyczne odpowiedzi / wszystkie odpowiedzi | 2/150 |

Nie należy rysować wspólnego wykresu „F1” z accuracy, recall i F1. Wyniki są
średnimi po trzech seedach, nie najlepszym seedem. Primary i risk-directed
shadow są osobnymi strumieniami; powtórzenia seedów nie są nowymi niezależnymi
przypadkami. Weryfikacja krytycznych odpowiedzi jest assisted/non-SME.

Evidence v1 ma `FAILED_EVIDENCE_THRESHOLDS`; shadow
`FAILED_SHADOW_THRESHOLDS`. Sprawdzenie 37 związanych hashami artefaktów
zamknięcia potwierdziło brak zmian. Nie przeprowadzono nowego treningu,
inferencji ani zmiany benchmarku w ramach tego review.

## 5. Poprawki narracyjne wymagane w nowej prezentacji

1. **FC-209:** wejście zawiera już `deterministic_check.result=27`. Mówimy
   „model dostał poprawny wynik 27 i mimo progu 5 zwrócił PASS”, nie „udowodniliśmy,
   że sam umie odjąć”. Źródła: `data/diagnostic/diagnostic_set_v1.jsonl`
   i `results/sprint4_2b/seed_20260827_diagnostic_v2.jsonl`. Było to development
   po doprecyzowaniu przypadku, nie końcowy chroniony test.
2. **Pamięć:** 7,551–7,552 GiB to `max_memory_allocated`. Licznik reserved
   raportuje dla Q1 18,830–22,062 GiB, więcej niż raportowane 11,94 GiB karty.
   Źródła nie wyjaśniają tej niespójności; nie przypisujemy jej bez dowodu
   konkretnemu mechanizmowi Windows/paging. Nie twierdzimy ani „wystarczy 8 GB”,
   ani „potrzeba 22 GB fizycznego VRAM”. Podajemy środowisko i nazwę licznika.
3. **Parametry:** używamy liczby 33 030 144 trenowanych parametrów. Raportowane
   1,475324% odnosi się do 2 238 840 320 parametrów widocznych przez pipeline
   po kwantyzacji (`sum(numel())`), nie do oryginalnej liczby wag modelu 4B.
4. **Demo:** aktualny artefakt ma 114,361 s. 102,343 s w historycznym M3 to
   starszy pomiar. Demo jest smoke testem pipeline'u, nie dowodem jakości.
5. **Guard:** blokuje wybrane sprzeczności; nie naprawia modelu i nie dowodzi
   pełnej odporności na injection. Samo `sources_valid=1` nie dowodzi,
   że cytowane źródło uzasadnia decyzję.

Nie przepisujemy historycznych raportów, goldów ani wyników. Nowy wykład
stosuje skorygowaną interpretację. Brak porównania full FT vs LoRA vs QLoRA
na tym samym budżecie: nie przypisujemy naszemu eksperymentowi wyniku,
którego nie zmierzył.

## 6. Ocena dla prowadzącego

- Sukces techniczny: tak, ukończone treningi i zgodne artefakty.
- Sukces na syntetycznym development: tak, ale na ograniczonej dystrybucji.
- Sukces protected benchmarku: nie.
- Dobry case do wykładu: tak — z widocznymi ograniczeniami, bez poprawiania
  wyniku po otwarciu testu i bez obietnicy autonomicznej kontroli bankowej.

Główna myśl: **„Nauczyliśmy adapter wykonywać format zadania. Dopiero trudne
przypadki pokazały, gdzie nie wolno powierzyć mu decyzji.”**

## Walidacja tego pakietu

- odczytowy audit: PASS dla pięciu biegów, z opisanymi zastrzeżeniami;
- walidacja istniejącego closure: `EVIDENCE_V1_CLOSED_READ_ONLY`;
- testy projektu: 91/91 PASS;
- agenda guide'a: 26 ciągłych sekcji, 56 minut treści + 4 minuty pytań;
- ścieżki źródeł w guide: istnieją;
- źródłowe PPTX, konfiguracje, dane i wyniki Sprintów 3/4/6: bez zmian;
- nowa talia 60-minutowa i jej pełny render: wykonane w S6.7-LB; wynik QA opisuje `docs/38_lecture60_presentation_qa_report.md`.
