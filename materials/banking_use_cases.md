# Katalog zastosowań PEFT w banku

Katalog służy do dyskusji warsztatowej. Nie stanowi oceny prawnej ani zgody na
wdrożenie. Im większy wpływ na klienta lub sprawozdawczość, tym silniejszy musi
być udział reguł deterministycznych, retrieval, niezależnej walidacji i człowieka.

| Przypadek | Wartość biznesowa | Rola PEFT | Co poza PEFT | Główne ryzyko |
|---|---|---|---|---|
| Kontrola sprawozdań finansowych | szybsze wykrywanie rozbieżności między tabelami i notami | stabilny JSON, taksonomia niezgodności, uzasadnienie | parser tabel, przeliczenia, progi, source guard, kontroler | fałszywy PASS i zła jednostka |
| Triage ustaleń audytowych | porządkowanie backlogu i spójne kategorie | klasyfikacja typu, severity i właściciela | RAG do polityk, workflow i human review | błędny priorytet lub właściciel |
| Analiza zgodności ujawnień | porównanie raportu z checklistą | stabilna struktura braków i cytatów | wersjonowana checklista, RAG, walidacja źródeł | nieaktualna norma i zmyślone źródło |
| Reklamacje klientów | szybsze kierowanie i szkic odpowiedzi | ton, format, kategoria i routing | system sprawy, RAG, redakcja PII, człowiek | nieuprawniona obietnica klientowi |
| Notatka kredytowa | spójny szkic na podstawie danych analityka | format, streszczenie argumentów, lista braków | silniki scoringowe, polityka kredytowa, zatwierdzenie człowieka | automatyzacja decyzji wysokiego wpływu |
| Podsumowanie alertu AML | redukcja czasu czytania materiału | streszczenie dowodów i struktura narracji | reguły AML, graph analytics, case management, analityk | pominięcie sygnału lub sugestia decyzji |
| Klasyfikacja procedur i kontroli | spójny katalog procesów | mapowanie do stabilnej taksonomii | RAG do aktualnej treści, owner danych | utrwalona zła etykieta |
| Regulatory reporting support | wykrywanie braków i przygotowanie komentarza | język uzasadnienia i format wyjątków | obliczenia, lineage, reconciliation, sign-off | błędna liczba lub raport bez ścieżki audytu |
| KYC document intake | ekstrakcja do ustalonego schematu i triage braków | format i klasy dokumentów | OCR, walidatory, sankcje, human review | błędna tożsamość lub brak dokumentu |
| Helpdesk pracowniczy | szybsze odpowiedzi o procedurach | styl i routing | RAG z wersją dokumentu i cytatami | odpowiedź na nieaktualnej polityce |

## Wzorzec Financial Control Copilot

1. Parser i reguły obliczają wartości, jednostki, okresy i progi.
2. RAG dostarcza aktualną procedurę i identyfikatory źródeł.
3. LLM + adapter proponuje status, typ kontroli, severity i uzasadnienie w JSON.
4. Guard porównuje decyzję z twardymi przesłankami i blokuje sprzeczności.
5. Kontroler zatwierdza albo odrzuca wynik; log zachowuje pełną ścieżkę.

Najlepszy pokaz warsztatowy: kontrola sprawozdania finansowego. Łączy dane
tabelaryczne, źródła, materialność, pięć statusów i koszt błędu. FC-209 pokazuje,
dlaczego poprawne obliczenie zapisane w uzasadnieniu nie gwarantuje poprawnej
decyzji modelu.

