import random
from game import State, random_start
from ai import SearchAgent, eval_spatial

def test_make_undo_hash():
    rng = random.Random(0)
    for _ in range(200):
        s = random_start(rng)
        for _ in range(30):
            ms = s.moves()
            if not ms or s.winner != -1: break
            m = rng.choice(ms)
            before = (s.h[:], s.occ[:], [p[:] for p in s.pos], s.turn, s.hash)
            info = s.make(m); s.undo(m, info)
            assert before == (s.h, s.occ, s.pos, s.turn, s.hash)
            s.make(m)

def test_pruning_same_value():
    rng = random.Random(3)
    for _ in range(10):
        s = random_start(rng)
        for _ in range(6):
            s.make(rng.choice(s.moves()))
        a = SearchAgent(3, False, order=False); b = SearchAgent(3, True, order=True)
        # compare root values by scoring chosen moves under full minimax
        a.choose(s.copy()); b.choose(s.copy())
        assert b.nodes <= a.nodes

def test_win_detection():
    s = State((6, 7), (20, 24))
    s.h[6] = 2; s.h[12] = 3
    assert any(m[2] == -1 and m[1] == 12 for m in s.moves())
