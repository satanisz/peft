# S6.7-LB — deck 60-minutowy: render i QA

## Artefakt

- Deck: `materials/PEFT_w_banku_lecture60_v1.pptx`
- Zakres: 26 slajdów, 56 minut narracji + 4 min Q&A.
- Źródło wizualne: istniejący deck warsztatowy; deck źródłowy pozostaje niezmieniony.
- Render: `materials/PEFT_w_banku_lecture60_v1/slide-1.png` … `slide-26.png`.
- Presenter guide: `materials/lecture60_presenter_guide.md`.

## Wynik QA

| Kontrola | Wynik |
|---|---|
| eksport PPTX | PASS |
| liczba slajdów | 26 |
| pełny raster render | PASS (26/26) |
| test overflow / clipping | PASS — `slides_test.py` |
| fidelity do zatwierdzonego wzorca | PASS — układ, typografia i paleta zachowane |
| notatki źródłowe | PASS — 26/26 slajdów |
| zgodność liczb z audytem treningu | PASS — wartości Q0/Q1, seedy, czasy, pamięć, benchmark i Evidence v1 sprawdzone |
| live training / live inference w decku | NO — wykład używa wyników zamrożonych artefaktów |
| protected evidence | READ-ONLY; brak rerunu i retuningu |

## Decyzja

Artefakt jest gotowy do końcowego review prowadzącego. Nie jest to obietnica jakości produkcyjnej adaptera: Evidence v1 pozostaje `FAILED / FROZEN / READ-ONLY`, a negatywny benchmark jest częścią narracji dydaktycznej.
