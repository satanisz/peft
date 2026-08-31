# Materiały wykładu i archiwum warsztatu

## Bieżący wykład 60 minut

[Guide prowadzącego](lecture60_presenter_guide.md) zawiera 26 slajdów,
56 minut treści i 4 minuty pytań. Narracja bazuje na wykonanym treningu;
wykład nie wymaga notebooków, GPU ani live demo.

Nowy PPTX nie został jeszcze zbudowany. Kolejny krok:
[S6.7-LB — skład i QA](../docs/37_lecture60_delivery_plan.md).
Korekty interpretacji wyników zawiera
[review treningu](../docs/36_lecture60_training_review.md).

## Zachowana talia warsztatowa

`PEFT_LoRA_QLoRA_w_banku_workshop.pptx` zawiera 53 slajdy na 180-minutowe
szkolenie. Każdy slajd ma notatki prowadzącego z czasem, celem, przebiegiem,
przejściem lub pytaniem oraz blokiem źródeł.

Talia wykorzystuje wyniki projektu do opowiedzenia jednej historii: od wyboru
interwencji i mechaniki LoRA/QLoRA, przez dane graniczne i trening, po benchmark,
przypadek FC-209, deterministic guard i model odpowiedzialności w banku.

## Pakiet uczestnika i prowadzącego

- `quick_reference_lora_qlora.md` — dwustronicowa ściąga merytoryczna,
- `workshop_exercises.md` — karty trzech ćwiczeń i zadania dodatkowego,
- `trainer_answer_key.md` — odpowiedzi, rubryka i pytania do debriefu,
- `faq_troubleshooting.md` — FAQ, diagnostyka i twardy fallback demo,
- `banking_use_cases.md` — portfel zastosowań oraz wzorzec Financial Control Copilot,
- `workshop_checklist.md` — checklista dnia poprzedniego, startu i zakończenia.

Pełna agenda, mapa slajdów, trzy ćwiczenia, runbook demonstracji i fallback są
opisane w `docs/18_sprint_5_narrative_and_scenarios.md`. Trzy notebooki w
`notebooks/` prowadzą od wyboru interwencji i danych, przez QLoRA demo, do
benchmarku i deterministic guard.

Raport aktualizacji i walidacji znajduje się w
`docs/19_sprint_5_material_update_report.md`.

## Status i rozróżnienie wersji

S6.6A technicznie przeszło, a właściciel potwierdził bezproblemowe uruchamianie
sekcji. Aktualna zmiana formatu nie stanowi wstecznego zaliczenia 180-minutowej
próby warsztatu. Evidence v1 zostało już skonsumowane i jest zamrożone po
nieprzejściu progów; nie uruchamiamy go ponownie. Historyczny stan HOLD
w oryginalnej talii należy czytać razem z osobnym appendixem evidence,
nie jako stan bieżący projektu. Materiały nie stanowią zgody produkcyjnej.
