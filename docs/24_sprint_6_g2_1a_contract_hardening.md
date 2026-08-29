# Sprint 6 — G2.1A Contract, runner and reporting hardening

**Data:** 29 sierpnia 2026

**Model:** Sol/high

**Decyzja:** `READY_FOR_G2_1B_TECHNICAL_REHEARSAL_WITH_PROTECTED_HOLD`

## Cel

Etap naprawia trzy luki wykryte w review G0/G1/G2 bez odczytu protected
evidence: mutowanie zamrożonego kontraktu podczas approval, brak shadow
challenge w runnerze oraz brak wspólnego raportowania primary/shadow.

## Zmiany kontraktu approval

`configs/sprint6_evidence_gate_v1.json` pozostaje niezmiennym kontraktem HOLD
zamrożonym w G0. Decyzja Sol/high będzie zapisana osobno w
`results/sprint6/protected_open_approval.json` i musi wiązać dokładne hashe:

- kontraktów, progów, policy, schema i guardów,
- raportów G0/G1/G2.1,
- shadow datasetu, registry i review goldów,
- runnera, inferencji, metryk, guarda i raportowania.

Walidator wymaga również tagów G0/G1/G2 oraz przyszłego `s6-g2.1-pass`,
czystego Git, nazwanego review Sol/high i commita będącego przodkiem bieżącego
HEAD. Approval nadal nie konsumuje jawnego potwierdzenia operatora.

## Runner

Kolejność wykonania jest teraz split-first i zgodna z planem:

1. original test: 100 × 3 seedy,
2. boundary test: 120 × 3 seedy,
3. primary challenge: 20 × 3 seedy,
4. shadow challenge: 50 × 3 seedy.

Każda inferencja używa prompt contract v2, `max_new_tokens=384` i zapisuje
wszystkie seedy. Wznowienie uznaje etap za kompletny tylko przy zgodnym count,
adapterze, prompt contract, limicie tokenów i jawnej autoryzacji.

Shadow przechodzi następnie przez source/severity/deterministic guard. Jedenaście
przypadków z kontrolą deterministyczną ma zamrożone przed pierwszą inferencją
reguły trójpasmowe: ≤0,5 PASS, ≤5 WARN, >5 FAIL.

## Raportowanie

Nowy raport Sprintu 6 rozdziela primary protected evidence od risk-directed
shadow evidence. Egzekwuje wszystkie zamrożone progi shadow, w tym trzy seedy,
recall statusów, unsafe PASS, schema, severity, source integrity, deterministic
mismatch detection, false-block guarda i brak zaakceptowanych odpowiedzi
zablokowanych. Nawet pełne progi automatyczne pozostawiają
`PENDING_MANUAL_REVIEW` do review 150/150 odpowiedzi.

## Walidacja

- 85 testów PASS,
- 11/11 przypadków deterministycznych ma dokładnie jedną regułę,
- runner bez osobnego approval kończy się przed utworzeniem autoryzacji i przed
  odczytem protected evidence,
- protected outputs i authorization nadal nie istnieją.

## Wynik kolejnego kroku

G2.1B zostało wykonane na Luna/low i osiągnęło `S6_G2_1_PASS`: realny
local-only load, kontrolowane wstrzyknięcia awarii, wykonanie notebooków z
`RUN_TRAINING=False` oraz próba czystego środowiska przeszły. Szczegóły zawiera
[`25_sprint_6_g2_1b_technical_hardening_report.md`](25_sprint_6_g2_1b_technical_hardening_report.md).
Po tagu `s6-g2.1-pass` Sol/high może wykonać osobny review approval. Protected
evidence pozostaje HOLD.
