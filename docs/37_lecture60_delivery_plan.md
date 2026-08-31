# S6.7-L — wydanie wykładu 60-minutowego

## Zatwierdzona zmiana zakresu

Właściciel zmienił warsztat na wykład oparty wyłącznie na prezentacji,
określił czas 60 minut i potwierdził, że wykład ma bazować na wykonanym
treningu. Jego potwierdzenie „mieści się” zapisujemy jako akceptację czasu
slotu, **nie jako fikcyjny pomiar 180-minutowej ani nowej 60-minutowej próby**.

Ten plan zastępuje dla bieżącego wydania część release'ową dokumentów 29,
34 i 35. Kryterium 175–185 minut dotyczyło dawnego warsztatu i nie obowiązuje
wykładu. Nie trzeba go sztucznie zaliczać. Dawny warsztat pozostaje osobnym,
niezmienionym zasobem; nie nadajemy mu wstecz statusu pełnego dry-run PASS.

## Aktualny stan i produkty

- Gotowe: odczytowy review treningów w `docs/36_lecture60_training_review.md`.
- Gotowe: liczby i krzywe do slajdów w `results/lecture60/training_audit.json`.
- Gotowe: narracja, sekwencja i notatki do 26 slajdów w
  `materials/lecture60_presenter_guide.md`.
- Do wykonania: osobny `materials/PEFT_w_banku_lecture60_v1.pptx`.
- Do wykonania: pełny render, fidelity QA i kontrola treści gotowego decku.
- Do wykonania: akceptacja gotowego wykładu, manifest i release.

Nie deklarujemy gotowego PPTX ani PASS renderu na podstawie samej narracji.

## S6.7-LA — narracja i review treningu

Wykonanie: Sol/high. Rezultat obecnego kroku: `LECTURE60_NARRATIVE_READY`.

Wykład pokazuje: 640 przykładów Q1; trzy seedy; 240 kroków; około 86 minut
na seed; sukces na development; niepowodzenie protected i shadow evidence.
Obowiązkowe korekty interpretacji opisano w review: FC-209 z podanym wynikiem
deterministycznym, allocated vs reserved, mianownik procentu parametrów,
nieizolowana ablacja Q0/Q1 i aktualny czas demo.

## S6.7-LB — złożenie i walidacja, Luna/low

1. Przeczytaj review oraz cały guide. Nie prowadź nowych eksperymentów.
2. Wykonaj `uv run python scripts/audit_lecture_training.py`. Jeśli audit
   zgłosi niezgodność hashów, zatrzymaj się; nie aktualizuj źródłowych hashów,
   by ukryć zmianę. Brak lokalnych wag oznacza brak ich ponownej weryfikacji,
   a nie błąd dowodu historycznego; zgłoś to zamiast pobierać/trenować model.
3. Użyj umiejętności Presentations. Zbadaj pełny deck 53 slajdów i appendix
   4 slajdów. Zachowaj wzorzec wizualny i hierarchię master/layout.
   Własny wykład powstaje jako kopia, nie nadpisanie oryginałów.
4. Przygotuj mapę source-slide → output-slide i edycji obiektów, następnie
   zbuduj 26 slajdów. Stara mapa tematów nie zastępuje inspekcji PPTX.
5. Wykorzystaj rzeczywiste liczby i krzywe. Podpisuj train loss, zbiór,
   metrykę, liczność i sposób agregacji. Nie kopiuj błędnych uproszczeń
   z historycznych tytułów. Wykres loss: trzy Q1, pełne zapisane punkty;
   nie Q0, nie demo i nie arbitralny „najlepszy seed”.
6. Wstaw notatki z guide'a i źródła każdego slajdu. Usuń z widocznego tekstu
   polecenia dla modeli, numery sprintów, stare oznaczenia „protected HOLD”
   jako stan bieżący, timingi oraz instrukcje live demo.
7. Wykonaj pełny render i review każdego slajdu w pełnym rozmiarze,
   sprawdzenie overflow/placeholderów/fidelity i kontrolę liczb. Sama
   poprawność ZIP nie jest walidacją wizualną.
8. Zapisz `docs/38_lecture60_delivery_and_qa_report.md` oraz maszynowy raport
   QA w `results/lecture60/`. Sprawdź, że hashe obu źródłowych PPTX i closure
   pozostały identyczne. Uruchom testy projektu.
9. Zatrzymaj się na `LECTURE60_READY_FOR_FINAL_REVIEW`. Na tym kroku nie
   twórz finalnego tagu i nie ogłaszaj M6 PASS.

### Punkty startowe selekcji tematów

To indeks treści, nie gotowa mapa obiektów. Po inspekcji dobierz odpowiedni
odziedziczony układ i skróć copy zamiast zmniejszać fonty.

| Nowe slajdy | Treści w starej talii / appendixie |
|---|---|
| 1–5: problem, kontrakt, dane | stare 1–8, 28–32; FC-209 także 46 |
| 6–11: LoRA/QLoRA i zasoby | stare 10–16, 19–24, 36–37 |
| 12–15: loss, czas, checkpoint | stare 34–39; krzywe z audytu |
| 16–19: validation i ograniczenia | stare 30, 32, 41–47 |
| 20–23: primary i shadow | appendix A1–A3 plus zamrożone raporty |
| 24–26: bank i zakończenie | stare 49–53; appendix A4 |

Pomiń live demo, przerwę, pracę w grupach, plan 90 dni i długi katalog metod.
Wykład ma pozostać opowieścią o wykonanym treningu, a nie skróconym spisie
treści wszystkich sprintów.

## S6.7-LC — końcowy review i akceptacja

Sol/high sprawdza gotową talię, nie tylko plan. Bramki:

- teoria wyjaśnia faktyczną konfigurację; brak sugerowanego benchmarku metod,
  których nie testowano;
- widać poprawny wynik deterministyczny wejścia FC-209 i błędną decyzję Q1;
- wszystkie seedy i oba strumienie evidence są reprezentowane;
- 11/60 primary i 2/150 shadow nie znikają podczas skracania;
- brak obietnicy karty 8 GB, pełnego resume optymalizatora, izolacji wpływu
  danych i „1,48% oryginalnego 4B”;
- materiały ujawniają syntetyczność danych i non-SME assisted review;
- brak live training/inference oraz brak nowego evidence runu;
- plan treści sumuje się do 56 minut plus 4 minuty pytań;
- właściciel akceptuje konkretną wersję pliku do 60-minutowego wykładu.

Nie wymagać pomiaru pełnych 3 godzin. W artefakcie akceptacji rozdzielić:
`planned_minutes=60`, `owner_accepts_lecture_scope=true`,
`measured_delivery_minutes` (null, jeśli nie mierzono) i
`full_delivery_rehearsal_measured=false`, gdy brak takiego pomiaru.
Krótka próba przejść i tempa jest rekomendowana, ale nie udajemy obowiązkowego
historycznego testu czasowego.

## S6.7-LD — mechaniczny release po akceptacji, Luna/low

- Manifest `results/lecture60/release_manifest.json` wiąże SHA-256 finalnego
  decku, guide'a, review treningu, audytu, raportów QA i źródeł evidence.
- Osobny artefakt `results/lecture60/m6_lecture_release.json`:
  `M6_LECTURE_READY_NOT_FOR_PRODUCTION`, format `lecture`, slot 60 minut,
  źródło jawnej akceptacji, brak live demo i brak production approval.
- Wagi adaptera i modele nie trafiają do Git ani do pakietu wykładowego;
  manifest wskazuje ich istniejące audytowe hashe jako provenance, nie jako
  pliki dostarczone uczestnikom.
- Powtórz testy/integrity checks, wykonaj commit i push, dopiero potem
  annotated tag `lecture-v1.0` wskazujący zweryfikowany release commit.
- Nie twórz `workshop-v1.0`: byłby mylącą nazwą dla nowego produktu.
- Nie modyfikuj acceptance S6.5A, closure, goldów, seedów ani progów.

## Polecenie następnego kroku

„Wykonaj S6.7-LB zgodnie z docs/37_lecture60_delivery_plan.md. Zbuduj osobny
26-slajdowy wykład na podstawie materials/lecture60_presenter_guide.md i
zweryfikowanych wyników treningu. Pełny render, fidelity QA i kontrola liczb.
Bez treningu, inferencji i release tagu; zatrzymaj się przed końcowym review”.
