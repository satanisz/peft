# Materiały Sprintu 5

## Talia warsztatowa

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

## Status bramki

Trening demonstracyjny i fresh reload zakończyły się poprawnie. Pakiet jest
kandydatem do M5 Content freeze i wymaga jeszcze pełnej próby 180 minut w
Sprincie 6. Protected evidence pozostaje zamknięte; materiał szkoleniowy nie
jest zgodą produkcyjną.
