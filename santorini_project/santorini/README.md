# Intelligent Santorini Player (AI310/CS361 Project 6)

Files: `gui.py` (Tkinter GUI: `python gui.py`), `game.py` (engine/state), `ai.py` (agents + heuristics), `play.py` (human vs AI),
`experiments.py` (-> `results.md`), `test_game.py`.

Run: `python play.py --time 1.0`   |   `python experiments.py 10`

## Design
- **State**: flat 25-int height list (0-3, 4 = dome), 25-cell occupancy list, 2x2 worker positions,
  64-bit Zobrist hash updated incrementally; in-place `make`/`undo` (no copying in search); precomputed neighbour tables.
- **Moves**: (worker, destination, build). Climb at most +1, no domes/occupied cells. Stepping on level 3 wins
  (generated first, build = -1). A player with no legal move loses.
- **Search**: explicit Minimax; Alpha-Beta with move ordering; iterative-deepening negamax alpha-beta with a
  transposition table, time limit per move.
- **Heuristic (spatial)**: height of workers (0/12/40), centre control, mobility, "threat" (worker on level 2 next to
  free level 3), nearby towers, penalty for being trapped on the ground floor / low mobility, and an immediate-win/loss
  check for the side to move. Weights are parameters of `make_eval`.
