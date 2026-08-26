# Boundary baseline — validation

| Wariant | Schemat | Accuracy | Macro-F1 | WARN recall | N/A recall | Pair accuracy | FAIL FPR | Unsafe PASS | Escalation | Śr. koszt | Input tok. | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 | 97.5% | 48.3% | 0.479 | 46.7% | 53.3% | 23.3% | 32.4% | 14.7% | 37.8% | 2.24 | 1057 | 8.09 |
| B2 | 100.0% | 60.8% | 0.606 | 76.7% | 66.7% | 38.3% | 43.8% | 1.3% | 51.1% | 1.61 | 2683 | 10.35 |
| B3 | 100.0% | 90.8% | 0.894 | 93.3% | 100.0% | 81.7% | 8.6% | 2.7% | 7.8% | 0.38 | 2897 | 10.54 |

Najwyższe macro-F1: **B3**.
Najniższy średni koszt błędu: **B3**.

Wynik dotyczy diagnostycznego boundary pack, a nie częstości produkcyjnych.
