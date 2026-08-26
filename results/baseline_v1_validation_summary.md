# Baseline v1 — validation

| Wariant | N | JSON | Schemat | Status accuracy | Macro-F1 | Źródła | FAIL FPR | Latencja p95 | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 | 50 | 100.0% | 0.0% | 12.0% | 0.109 | 98.0% | 0.0% | 14.85 s | 7.65 GiB |
| B1 | 50 | 100.0% | 100.0% | 46.0% | 0.349 | 100.0% | 20.0% | 14.67 s | 8.04 GiB |
| B2 | 50 | 100.0% | 100.0% | 72.0% | 0.529 | 100.0% | 14.3% | 17.62 s | 9.86 GiB |

Najwyższe macro-F1 na tym splicie uzyskał **B2**. Wybór baseline'u do porównań z adapterem musi dodatkowo uwzględniać schema validity, false positive rate i koszt kontekstu.

## Katalog błędów

- B0: 50 przypadków z błędnym schematem lub statusem.
- B1: 27 przypadków z błędnym schematem lub statusem.
- B2: 14 przypadków z błędnym schematem lub statusem.

Szczegóły per przypadek znajdują się w odpowiadającym pliku JSON.
