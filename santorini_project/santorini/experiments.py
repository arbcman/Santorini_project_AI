"""Experiments: (1) minimax vs alpha-beta node counts, (2) heuristic comparison,
(3) depth comparison, (4) iterative-deepening/TT agent.  Writes results.md."""
import random, time, sys
from game import State, random_start
from ai import SearchAgent, IDAgent, RandomAgent, eval_simple, eval_spatial, make_eval


def play(a0, a1, rng, max_plies=200):
    s = random_start(rng)
    ag = (a0, a1)
    for ply in range(max_plies):
        if not s.moves():
            return 1 - s.turn
        s.make(ag[s.turn].choose(s))
        if s.winner != -1:
            return s.winner
    return -1


def match(mk0, mk1, games, seed=0):
    """Alternate which agent plays first; returns (wins0, wins1, draws)."""
    rng = random.Random(seed)
    w = [0, 0, 0]
    for g in range(games):
        a, b = mk0(), mk1()
        st = random.Random(rng.random())
        if g % 2 == 0:
            r = play(a, b, st); r = r if r < 0 else (0 if r == 0 else 1)
        else:
            r = play(b, a, st); r = r if r < 0 else (1 if r == 0 else 0)
        w[2 if r < 0 else r] += 1
    return w


def positions(n, plies, seed):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        s = random_start(rng)
        ok = True
        for _ in range(plies):
            ms = s.moves()
            if not ms: ok = False; break
            s.make(rng.choice(ms))
            if s.winner != -1: ok = False; break
        if ok and s.moves(): out.append(s)
    return out


def main():
    out = []
    P = out.append
    P("# Santorini experiments\n")
    # 1. pruning
    P("## 1. Minimax vs Alpha-Beta (same eval, same depth, 8 mid-game positions)\n")
    P("| depth | Minimax nodes | AlphaBeta nodes (no ordering) | AlphaBeta nodes (ordered) | reduction |")
    P("|---|---|---|---|---|")
    ps = positions(8, 8, 1)
    for d in (1, 2, 3):
        tot = [0, 0, 0]
        for s in ps:
            for i, ag in enumerate((SearchAgent(d, False, order=False, seed=0),
                                    SearchAgent(d, True, order=False, seed=0),
                                    SearchAgent(d, True, order=True, seed=0))):
                ag.choose(s.copy()); tot[i] += ag.nodes
        P(f"| {d} | {tot[0]} | {tot[1]} | {tot[2]} | {100*(1-tot[2]/tot[0]):.1f}% |")
    # 2. heuristics
    G = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    P(f"\n## 2. Heuristic comparison (depth 3 alpha-beta both sides, {G} games, random starts, colours alternated)\n")
    P("| A | B | A wins | B wins | draws |"); P("|---|---|---|---|---|")
    heur = {"Spatial": eval_spatial, "HeightOnly": eval_simple,
            "Spatial-noThreat": make_eval(w_threat=0, w_adjhigh=0),
            "Spatial-noTrap": make_eval(w_trap=0)}
    for nb in ("HeightOnly", "Spatial-noThreat", "Spatial-noTrap"):
        w = match(lambda: SearchAgent(3, evaluate=heur["Spatial"], seed=1),
                  lambda nb=nb: SearchAgent(3, evaluate=heur[nb], seed=2), G)
        P(f"| Spatial | {nb} | {w[0]} | {w[1]} | {w[2]} |")
    # 3. depth
    P(f"\n## 3. Search depth (spatial heuristic, {G} games)\n")
    P("| A | B | A wins | B wins | draws |"); P("|---|---|---|---|---|")
    for da, db in ((1, 2), (2, 3), (1, 3)):
        w = match(lambda da=da: SearchAgent(da, seed=1), lambda db=db: SearchAgent(db, seed=2), G)
        P(f"| depth {da} | depth {db} | {w[0]} | {w[1]} | {w[2]} |")
    # 4. baselines
    P(f"\n## 4. Against baselines ({G} games)\n")
    P("| A | B | A wins | B wins | draws |"); P("|---|---|---|---|---|")
    w = match(lambda: SearchAgent(3, seed=1), lambda: RandomAgent(2), G)
    P(f"| AlphaBeta d=3 | Random | {w[0]} | {w[1]} | {w[2]} |")
    w = match(lambda: IDAgent(0.15, seed=1), lambda: SearchAgent(3, seed=2), G)
    P(f"| ID-AB 0.15s/move + TT | AlphaBeta d=3 | {w[0]} | {w[1]} | {w[2]} |")
    # 5. depth reached by ID
    s = State(); ag = IDAgent(1.0)
    ag.choose(s)
    P(f"\n## 5. Iterative deepening, opening position, 1 s budget\n\nDepth reached: {ag.depth_reached}, nodes: {ag.nodes}\n")
    open("results.md", "w").write("\n".join(out)); print("\n".join(out))


if __name__ == "__main__":
    main()
