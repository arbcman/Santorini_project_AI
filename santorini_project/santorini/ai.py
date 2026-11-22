"""Search agents: Random, Greedy, plain Minimax, Alpha-Beta, and an
iterative-deepening Alpha-Beta with transposition table + move ordering."""
import random
import time
from game import State, NEIGH, CELLS

WIN = 100000
CENTER = [0] * CELLS
for _i in range(CELLS):
    _r, _c = divmod(_i, 5)
    CENTER[_i] = 2 - max(abs(_r - 2), abs(_c - 2))     # 2 centre .. 0 edge

# ---------------------------------------------------------------- heuristics
H_PTS = (0, 12, 40, 0)   # value of standing on level 0/1/2 (3 = win, handled by search)


def eval_simple(s, me):
    """H1: only worker heights (baseline)."""
    opp = 1 - me
    return (sum(s.h[c] for c in s.pos[me]) - sum(s.h[c] for c in s.pos[opp])) * 10


def make_eval(w_height=1.0, w_mob=1.5, w_center=2.0, w_threat=60.0,
              w_trap=25.0, w_adjhigh=3.0):
    """H2 factory: spatial heuristic (high ground, mobility, threats, trapped)."""
    def evaluate(s, me):
        h, occ = s.h, s.occ
        opp = 1 - me
        # side to move can win immediately / is about to lose
        if s.has_win_next(s.turn):
            return WIN // 2 if s.turn == me else -WIN // 2
        score = 0.0
        for p, sign in ((me, 1), (opp, -1)):
            for src in s.pos[p]:
                hs = h[src]
                score += sign * w_height * H_PTS[hs]
                score += sign * w_center * CENTER[src]
                mob = 0
                up = 0
                threat = 0
                for d in NEIGH[src]:
                    hd = h[d]
                    if hd < 4 and occ[d] == -1 and hd <= hs + 1:
                        mob += 1
                        if hd > hs:
                            up += 1
                        if hs == 2 and hd == 3:
                            threat += 1
                    if hd == 3 and occ[d] == -1:
                        score += sign * w_adjhigh * (hs >= 1)  # tall tower nearby
                score += sign * w_mob * mob
                score += sign * w_threat * threat       # workers one step from winning
                if hs == 0 and mob <= 2:                # trapped on the ground floor
                    score -= sign * w_trap * (3 - mob)
                elif mob == 0:
                    score -= sign * w_trap * 3
        return score
    return evaluate


eval_spatial = make_eval()

# ---------------------------------------------------------------- agents


class Agent:
    name = "agent"
    nodes = 0

    def choose(self, s):
        raise NotImplementedError


class RandomAgent(Agent):
    name = "Random"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def choose(self, s):
        ms = s.moves()
        for m in ms:
            if m[2] == -1:
                return m
        return self.rng.choice(ms)


class SearchAgent(Agent):
    """Fixed-depth minimax (prune=False) or alpha-beta (prune=True)."""

    def __init__(self, depth=3, prune=True, evaluate=eval_spatial, order=True, seed=None):
        self.depth, self.prune, self.evaluate, self.order = depth, prune, evaluate, order
        self.rng = random.Random(seed)
        self.name = f"{'AlphaBeta' if prune else 'Minimax'}(d={depth})"

    def _ordered(self, s, ms):
        """Move ordering: wins first, then climbing / central destinations."""
        if not self.order:
            return ms
        h = s.h
        return sorted(ms, key=lambda m: -10 ** 6 if m[2] == -1
                      else -(h[m[1]] * 4 + CENTER[m[1]] + (2 if h[m[2]] == 3 else 0)))

    def choose(self, s):
        self.nodes = 0
        self.me = s.turn
        ms = s.moves()
        best, best_v = [], -10 ** 9
        alpha = -10 ** 9
        for m in self._ordered(s, ms):
            info = s.make(m)
            v = self._min(s, self.depth - 1, alpha, 10 ** 9) if s.winner == -1 else WIN + self.depth
            s.undo(m, info)
            if v > best_v:
                best_v, best = v, [m]
            elif v == best_v:
                best.append(m)
            if self.prune and v > alpha:
                alpha = v
        return self.rng.choice(best)

    # MAX node: player `me` to move.  MIN node: opponent to move.
    def _max(self, s, d, a, b):
        self.nodes += 1
        ms = s.moves()
        if not ms:
            return -WIN - d                 # no legal move -> `me` loses
        if d == 0:
            return self.evaluate(s, self.me)
        v = -10 ** 9
        for m in self._ordered(s, ms):
            info = s.make(m)
            t = WIN + d if s.winner != -1 else self._min(s, d - 1, a, b)
            s.undo(m, info)
            if t > v:
                v = t
            if self.prune:
                if v >= b:
                    return v
                if v > a:
                    a = v
        return v

    def _min(self, s, d, a, b):
        self.nodes += 1
        ms = s.moves()
        if not ms:
            return WIN + d                  # opponent stuck -> `me` wins
        if d == 0:
            return self.evaluate(s, self.me)
        v = 10 ** 9
        for m in self._ordered(s, ms):
            info = s.make(m)
            t = -WIN - d if s.winner != -1 else self._max(s, d - 1, a, b)
            s.undo(m, info)
            if t < v:
                v = t
            if self.prune:
                if v <= a:
                    return v
                if v < b:
                    b = v
        return v


class IDAgent(Agent):
    """Iterative deepening alpha-beta (negamax form) + Zobrist transposition table,
    killer-free move ordering (TT move, then height gain / centre), time-limited."""

    def __init__(self, time_limit=1.0, max_depth=12, evaluate=eval_spatial, seed=None):
        self.tl, self.max_depth, self.evaluate = time_limit, max_depth, evaluate
        self.rng = random.Random(seed)
        self.name = f"ID-AB(t={time_limit}s)"
        self.tt = {}
        self.depth_reached = 0

    class _Timeout(Exception):
        pass

    def _order(self, s, ms, tt_move):
        h = s.h

        def key(m):
            if m == tt_move:
                return -10 ** 6
            if m[2] == -1:
                return -10 ** 7
            return -(h[m[1]] * 10 + CENTER[m[1]] * 2 + (3 if h[m[2]] == 3 else 0))
        return sorted(ms, key=key)

    def choose(self, s):
        s = s.copy()          # a timeout aborts mid-search without undoing moves
        self.nodes = 0
        self.t0 = time.time()
        self.deadline = self.t0 + self.tl
        if len(self.tt) > 400000:
            self.tt.clear()
        ms = s.moves()
        best = ms[0]
        if len(ms) == 1 or ms[0][2] == -1:
            return ms[0]
        for depth in range(1, self.max_depth + 1):
            try:
                v, m = self._root(s, ms, depth)
            except self._Timeout:
                break
            best = m
            self.depth_reached = depth
            if abs(v) >= WIN - 100:           # forced win/loss found
                break
        return best

    def _root(self, s, ms, depth):
        sign = 1
        alpha, beta = -10 ** 9, 10 ** 9
        e = self.tt.get(s.hash)
        ordered = self._order(s, ms, e[3] if e else None)
        best_v, best_m = -10 ** 9, ordered[0]
        for m in ordered:
            info = s.make(m)
            v = WIN + depth if s.winner != -1 else -self._nm(s, depth - 1, -beta, -alpha, s.turn)
            s.undo(m, info)
            if v > best_v:
                best_v, best_m = v, m
            if v > alpha:
                alpha = v
        self.tt[s.hash] = (depth, 0, best_v, best_m)
        return best_v, best_m

    def _nm(self, s, d, a, b, root_me):
        """Negamax; value is from the viewpoint of s.turn."""
        self.nodes += 1
        if self.nodes & 1023 == 0 and time.time() > self.deadline:
            raise self._Timeout
        a0 = a
        e = self.tt.get(s.hash)
        tt_move = None
        if e:
            tt_move = e[3]
            if e[0] >= d:
                if e[1] == 0:
                    return e[2]
                if e[1] == 1 and e[2] > a:
                    a = e[2]
                elif e[1] == 2 and e[2] < b:
                    b = e[2]
                if a >= b:
                    return e[2]
        ms = s.moves()
        if not ms:
            return -WIN - d
        if d == 0:
            return self.evaluate(s, s.turn)
        best_v, best_m = -10 ** 9, None
        for m in self._order(s, ms, tt_move):
            info = s.make(m)
            v = WIN + d if s.winner != -1 else -self._nm(s, d - 1, -b, -a, root_me)
            s.undo(m, info)
            if v > best_v:
                best_v, best_m = v, m
            if v > a:
                a = v
            if a >= b:
                break
        flag = 0 if a0 < best_v < b else (1 if best_v >= b else 2)
        self.tt[s.hash] = (d, flag, best_v, best_m)
        return best_v
