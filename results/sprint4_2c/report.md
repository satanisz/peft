# Sprint 4.2C — deterministic decision containment

**Decyzja demonstracyjna:** `READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD`

**Protected evidence:** `HOLD`

Guard nie poprawia odpowiedzi. Sprzeczny wynik zachowuje do audytu i kieruje do człowieka.

| Seed | Pass-through | Blokady | Reguła FC-209 | Wynik |
|---:|---:|---:|---:|---|
| 20260827 | 29/30 | 1 | 27 GT 5 | PASS → blokada (FAIL) |
| 20260828 | 29/30 | 1 | 27 GT 5 | PASS → blokada (FAIL) |
| 20260829 | 29/30 | 1 | 27 GT 5 | PASS → blokada (FAIL) |

Regułę utworzono po analizie diagnostycznej. Jest materiałem warsztatowym i nie stanowi niezależnego dowodu generalizacji.
Protected splits pozostają nieotwarte.
