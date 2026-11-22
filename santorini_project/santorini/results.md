# Santorini experiments

## 1. Minimax vs Alpha-Beta (same eval, same depth, 8 mid-game positions)

| depth | Minimax nodes | AlphaBeta nodes (no ordering) | AlphaBeta nodes (ordered) | reduction |
|---|---|---|---|---|
| 1 | 482 | 482 | 482 | 0.0% |
| 2 | 28163 | 8360 | 4608 | 83.6% |
| 3 | 1683726 | 157174 | 67651 | 96.0% |

## 2. Heuristic comparison (depth 3 alpha-beta both sides, 10 games, random starts, colours alternated)

| A | B | A wins | B wins | draws |
|---|---|---|---|---|
| Spatial | HeightOnly | 10 | 0 | 0 |
| Spatial | Spatial-noThreat | 8 | 2 | 0 |
| Spatial | Spatial-noTrap | 4 | 6 | 0 |

## 3. Search depth (spatial heuristic, 10 games)

| A | B | A wins | B wins | draws |
|---|---|---|---|---|
| depth 1 | depth 2 | 4 | 6 | 0 |
| depth 2 | depth 3 | 4 | 6 | 0 |
| depth 1 | depth 3 | 0 | 10 | 0 |

## 4. Against baselines (10 games)

| A | B | A wins | B wins | draws |
|---|---|---|---|---|
| AlphaBeta d=3 | Random | 10 | 0 | 0 |
| ID-AB 0.15s/move + TT | AlphaBeta d=3 | 9 | 1 | 0 |

## 5. Iterative deepening, opening position, 1 s budget

Depth reached: 4, nodes: 57344
