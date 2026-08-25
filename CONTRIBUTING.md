# Współpraca nad projektem

## Gałęzie

- `main` — wersja działająca i możliwa do odtworzenia,
- `feature/<nazwa>` — kod i funkcjonalności,
- `experiment/<nazwa>` — konfiguracje i wyniki eksperymentów,
- `docs/<nazwa>` — materiały oraz dokumentacja,
- `fix/<nazwa>` — poprawki błędów.

## Commity

Stosujemy krótkie komunikaty:

- `feat: add synthetic variance cases`,
- `experiment: record qlora rank-16 results`,
- `fix: prevent split leakage`,
- `docs: add trainer notes for NF4`,
- `test: cover invalid evidence identifiers`,
- `chore: update locked dependencies`.

Jeden commit powinien reprezentować jedną logiczną zmianę. Wyniki eksperymentu
muszą wskazywać konfigurację, rewizję modelu, wersję danych i środowisko.

## Artefakty

Do Git trafiają:

- kod, testy i konfiguracje,
- dokumentacja,
- syntetyczne dane o rozsądnym rozmiarze,
- małe raporty JSON/CSV i wykresy wykorzystywane w szkoleniu.

Do zwykłego Git nie trafiają:

- wagi modeli,
- checkpointy i adaptery,
- cache Hugging Face,
- klucze, tokeny i pliki `.env`,
- surowe dane zawierające informacje poufne lub osobowe.

Ciężkie, zatwierdzone artefakty udostępniamy przez Git LFS albo jako assets
wydania. Każdy taki artefakt powinien mieć sumę SHA-256 i opis konfiguracji.

## Kontrola przed scaleniem

```powershell
uv run peft-workshop validate-data
uv run python -m unittest discover -s tests -v
```

Zmiany wpływające na dane lub benchmark muszą dodatkowo potwierdzić brak
przecieku między splitami.

