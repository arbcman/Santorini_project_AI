"""Santorini game engine with a compact, in-place make/undo state representation.

Board: 5x5 flattened to a 25-int list.  heights[i] in 0..4 (4 = dome).
occ[i] = -1 (empty) or player id (0/1).  pos[p] = [cell, cell] (two workers).
A move is a tuple (worker_index, destination, build_cell); build_cell == -1
when the move itself wins (stepping on level 3), because no build is needed.
Neighbour lists and Zobrist keys are precomputed so move generation is just
list lookups -> deep search in pure Python.
"""
import random

N = 5
CELLS = N * N
NEIGH = []
for _i in range(CELLS):
    r, c = divmod(_i, N)
    NEIGH.append(tuple(
        (r + dr) * N + (c + dc)
        for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        if (dr or dc) and 0 <= r + dr < N and 0 <= c + dc < N))

_rng = random.Random(12345)
Z_H = [[_rng.getrandbits(64) for _ in range(5)] for _ in range(CELLS)]
Z_W = [[_rng.getrandbits(64) for _ in range(CELLS)] for _ in range(2)]
Z_T = _rng.getrandbits(64)


class State:
    __slots__ = ("h", "occ", "pos", "turn", "hash", "winner")

    def __init__(self, p0=(6, 18), p1=(8, 16)):
        self.h = [0] * CELLS
        self.occ = [-1] * CELLS
        self.pos = [list(p0), list(p1)]
        self.turn = 0
        self.winner = -1
        self.hash = 0
        for p in (0, 1):
            for c in self.pos[p]:
                self.occ[c] = p
                self.hash ^= Z_W[p][c]
        for c in range(CELLS):
            self.hash ^= Z_H[c][0]

    # ---- move generation -------------------------------------------------
    def moves(self):
        """All legal moves for the player to move. Winning moves come first."""
        h, occ = self.h, self.occ
        me = self.turn
        wins, out = [], []
        for w in (0, 1):
            src = self.pos[me][w]
            hs = h[src]
            for dst in NEIGH[src]:
                hd = h[dst]
                if hd > hs + 1 or hd >= 4 or occ[dst] != -1:
                    continue
                if hd == 3:
                    wins.append((w, dst, -1))
                    continue
                for b in NEIGH[dst]:
                    if h[b] < 4 and (occ[b] == -1 or b == src):
                        out.append((w, dst, b))
        return wins + out if wins else out

    def has_win_next(self, player):
        """True if `player` could step onto a level-3 tower right now."""
        h, occ = self.h, self.occ
        for src in self.pos[player]:
            if h[src] < 2:
                continue
            for dst in NEIGH[src]:
                if h[dst] == 3 and occ[dst] == -1:
                    return True
        return False

    # ---- make / undo -----------------------------------------------------
    def make(self, m):
        w, dst, b = m
        me = self.turn
        src = self.pos[me][w]
        self.occ[src] = -1
        self.occ[dst] = me
        self.pos[me][w] = dst
        self.hash ^= Z_W[me][src] ^ Z_W[me][dst]
        prev_winner = self.winner
        if b == -1:
            self.winner = me
        else:
            hb = self.h[b]
            self.hash ^= Z_H[b][hb] ^ Z_H[b][hb + 1]
            self.h[b] = hb + 1
        self.turn = 1 - me
        self.hash ^= Z_T
        return (src, prev_winner)

    def undo(self, m, info):
        w, dst, b = m
        src, prev_winner = info
        me = 1 - self.turn
        self.turn = me
        self.hash ^= Z_T
        self.winner = prev_winner
        if b != -1:
            hb = self.h[b]
            self.hash ^= Z_H[b][hb] ^ Z_H[b][hb - 1]
            self.h[b] = hb - 1
        self.occ[dst] = -1
        self.occ[src] = me
        self.pos[me][w] = src
        self.hash ^= Z_W[me][src] ^ Z_W[me][dst]

    def copy(self):
        s = State.__new__(State)
        s.h = self.h[:]
        s.occ = self.occ[:]
        s.pos = [self.pos[0][:], self.pos[1][:]]
        s.turn, s.hash, s.winner = self.turn, self.hash, self.winner
        return s

    # ---- display ---------------------------------------------------------
    def __str__(self):
        rows = ["    " + "   ".join("ABCDE")]
        for r in range(N):
            cells = []
            for c in range(N):
                i = r * N + c
                lvl = "D" if self.h[i] == 4 else str(self.h[i])
                tok = ".XO"[self.occ[i] + 1] if self.occ[i] != -1 else " "
                cells.append(f"{lvl}{tok}".replace(" ", " "))
            rows.append(f" {r + 1}  " + "  ".join(cells))
        return "\n".join(rows)


def random_start(rng):
    cells = rng.sample(range(CELLS), 4)
    return State((cells[0], cells[1]), (cells[2], cells[3]))


def cell_name(i):
    r, c = divmod(i, N)
    return "ABCDE"[c] + str(r + 1)


def parse_cell(s):
    s = s.strip().upper()
    return (int(s[1]) - 1) * N + "ABCDE".index(s[0])
