# Checklista prowadzącego

## Dzień wcześniej

- [ ] Otwórz talię i sprawdź 53 slajdy oraz notatki.
- [ ] Sprawdź lokalny cache modelu, adapter Q1-DEMO i wolne miejsce.
- [ ] Uruchom test środowiska i fresh reload adaptera.
- [ ] Potwierdź `max_new_tokens=384` dla reloadu.
- [ ] Przygotuj zapisane wyniki Q1-DEMO i pełnego Q1 jako fallback.
- [ ] Nie otwieraj protected splits; obowiązuje `HOLD`.
- [ ] Wydrukuj lub udostępnij ściągę i karty ćwiczeń.

## 30 minut wcześniej

- [ ] Sprawdź GPU i zamknij procesy zużywające VRAM.
- [ ] Otwórz trzy notebooki, ale nie uruchamiaj treningu.
- [ ] Ustaw stoper na segmenty 10/15/25/30/15/43/20/12 minut.
- [ ] Miej pod ręką slajdy 34, 37, 40, 42, 46–48.

## Podczas demo

- [ ] Powiedz, że 12 kroków testuje pipeline, a nie jakość biznesową.
- [ ] Pokaż rozkład 10 przykładów na każdy status i zero truncation.
- [ ] Raportuj loss, peak VRAM i czas, ale nie interpretuj loss jako jakości.
- [ ] Pokaż manifest, zgodność bazy i fresh reload.
- [ ] Po 15 minutach przełącz się na fallback.

## Po szkoleniu

- [ ] Zapisz pytania uczestników i rozbieżne decyzje z ćwiczeń.
- [ ] Oznacz problemy treści, czasu i środowiska oddzielnie.
- [ ] Nie zmieniaj benchmarku na podstawie protected evidence.
- [ ] Aktualizuj materiały dopiero po klasyfikacji problemu.

