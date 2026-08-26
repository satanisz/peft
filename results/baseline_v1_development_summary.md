# Baseline v1 — development

| Wariant | N | JSON | Schemat | Status accuracy | Macro-F1 | Źródła | FAIL FPR | Latencja p95 | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 | 50 | 100.0% | 0.0% | 0.0% | 0.000 | 98.0% | 0.0% | 15.97 s | 7.65 GiB |
| B1 | 50 | 100.0% | 98.0% | 50.0% | 0.542 | 100.0% | 17.1% | 16.09 s | 8.04 GiB |
| B2 | 50 | 100.0% | 100.0% | 72.0% | 0.534 | 100.0% | 11.4% | 13.07 s | 9.87 GiB |

Najwyższe macro-F1 na tym splicie uzyskał **B1**. Wybór baseline'u do porównań z adapterem musi dodatkowo uwzględniać schema validity, false positive rate i koszt kontekstu.

## Katalog błędów

- B0: 50 przypadków z błędnym schematem lub statusem.
- B1: 26 przypadków z błędnym schematem lub statusem.
- B2: 14 przypadków z błędnym schematem lub statusem.

Szczegóły per przypadek znajdują się w odpowiadającym pliku JSON.
