"""Play Santorini in the terminal:  python play.py [--time 1.0] [--ai-first]"""
import argparse
from game import State, cell_name, parse_cell
from ai import IDAgent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", type=float, default=1.0)
    ap.add_argument("--ai-first", action="store_true")
    a = ap.parse_args()
    s = State()
    ai = IDAgent(time_limit=a.time)
    human = 1 if a.ai_first else 0
    print("You are", "XO"[human], "| enter: <worker cell> <destination> <build>  e.g. 'C2 C3 D3'")
    while True:
        print(s)
        ms = s.moves()
        if not ms:
            print("No legal moves - player", "XO"[s.turn], "loses."); break
        if s.turn == human:
            while True:
                try:
                    f, d, b = input("move> ").split()
                    f, d = parse_cell(f), parse_cell(d)
                    b = parse_cell(b) if b != "-" else -1
                    w = s.pos[human].index(f)
                    if (w, d, b) in ms: m = (w, d, b); break
                except Exception: pass
                print("illegal; use '-' as build when stepping onto level 3")
        else:
            m = ai.choose(s)
            print(f"AI: {cell_name(s.pos[s.turn][m[0]])} -> {cell_name(m[1])} build "
                  f"{cell_name(m[2]) if m[2] != -1 else '-'} (depth {ai.depth_reached}, {ai.nodes} nodes)")
        s.make(m)
        if s.winner != -1:
            print(s); print("Winner:", "XO"[s.winner]); break


if __name__ == "__main__":
    main()
