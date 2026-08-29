# Klucz prowadzącego i kryteria omówienia

## Ćwiczenie 1

| Przypadek | Odpowiedź oczekiwana | Co musi paść w uzasadnieniu |
|---|---|---|
| Zmienna procedura i cytaty | RAG | świeżość i traceability są problemem wiedzy |
| Niestabilne pięć statusów | PEFT/SFT po mocnym baseline | uczymy stabilnego zachowania i kontraktu |
| Nowe słownictwo w dużym korpusie | continued pretraining, często z RAG/SFT | szeroka adaptacja reprezentacji; nie obiecywać faktów bez retrieval |
| Jawna reguła liczbowa | kod deterministyczny | LLM może opisać wynik, ale nie powinien egzekwować progu |

Pełny punkt: poprawna metoda, przesłanka, ryzyko i test porównawczy. Pół punktu:
poprawna metoda bez mechanizmu. Zero: „fine-tuning wszystkiego” bez diagnozy.

## Ćwiczenie 2

- `PASS → WARN`: 0,4 vs 1,4 mln PLN przy progu ostrzegawczym 1 mln PLN.
- `WARN → FAIL`: ta sama niezgodność przechodzi przez próg materialności.
- `NOT_APPLICABLE → INSUFFICIENT_DATA`: brak triggera vs trigger obecny i brak źródła.

Nie akceptuj argumentu „brakuje danych, więc N/A”. `NOT_APPLICABLE` opisuje brak
zastosowania kontroli; `INSUFFICIENT_DATA` opisuje kontrolę właściwą, której nie
da się rozstrzygnąć. Dobra para różni się jedną przesłanką i zachowuje resztę
tekstu możliwie identyczną.

## Ćwiczenie 3

Oczekiwana decyzja: `HOLD` dla protected evidence oraz `READY_FOR_DEMO` dla
materiału szkoleniowego. Validation odpowiada na pytanie o znany rozkład. Guard
ogranicza znany błąd operacyjnie, ale powstał po analizie diagnostic, więc nie
jest niezależnym dowodem generalizacji i nie poprawia metryk adaptera.

Pytania do debriefu:

1. Co musiałoby się wydarzyć, aby zmienić `HOLD`?
2. Kto zatwierdza goldy i koszt błędu?
3. Które reguły należy przenieść do kodu przed kolejnym benchmarkiem?
4. Czy błąd FC-209 to problem danych, promptu, modelu czy architektury? Odpowiedź:
   częściowo wszystkich, ale jego bezpieczne opanowanie jest zadaniem systemu.

## Ćwiczenie dodatkowe — rubryka 0–10

- 0–2: baseline naprawdę testuje brak PEFT,
- 0–2: split jest po rodzinie, kliencie, dokumencie lub czasie — stosownie do ryzyka,
- 0–2: metryki obejmują format, semantykę i koszt biznesowy,
- 0–2: minimalne pary izolują przesłankę decyzyjną,
- 0–2: bramka, guard i human review mają jawnego właściciela.

## Prowadzenie dyskusji

Najpierw pytaj o decyzję, potem o dowód, a na końcu o ograniczenie. Nie pozwól,
aby rozmowa zatrzymała się na lossie, rozmiarze adaptera albo pojedynczym F1.
Wszystkie wyniki projektu dotyczą danych syntetycznych i demonstracji.

