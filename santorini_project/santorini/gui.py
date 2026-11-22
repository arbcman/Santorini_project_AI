"""Tkinter GUI:  python gui.py [--time 1.0] [--ai-first]
Click one of your workers, click a highlighted destination, then click a highlighted build cell
(stepping onto level 3 wins immediately, no build needed)."""
import argparse
import threading
import tkinter as tk
from game import State, N, cell_name
from ai import IDAgent

CELL = 100
COLORS = ["#e8f1f8", "#cfe0ee", "#a9c6de", "#7da6c9"]   # level 0..3 fill
WORKER = ["#d9381e", "#1d4ed8"]


class App:
    def __init__(self, root, tl, ai_first):
        self.root = root
        self.ai = IDAgent(time_limit=tl)
        self.human = 1 if ai_first else 0
        self.tl = tl
        self.top = tk.Frame(root); self.top.pack(fill="x")
        self.status = tk.Label(self.top, font=("Arial", 13), anchor="w")
        self.status.pack(side="left", padx=8, pady=6)
        tk.Button(self.top, text="New game", command=self.new).pack(side="right", padx=8)
        self.canvas = tk.Canvas(root, width=N * CELL, height=N * CELL, bg="white", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click)
        self.new()

    def new(self):
        self.s = State()
        self.sel_w = None; self.sel_dst = None
        self.busy = False
        self.gen = getattr(self, "gen", 0) + 1
        self.last = None
        self.legal = self.s.moves()
        self.draw()
        if self.s.turn != self.human:
            self.ai_turn()

    # ---- interaction --------------------------------------------------
    def click(self, e):
        if self.busy or self.s.winner != -1 or self.s.turn != self.human or not self.legal:
            return
        c = (e.y // CELL) * N + e.x // CELL
        me = self.human
        if self.sel_w is None:
            if c in self.s.pos[me]:
                w = self.s.pos[me].index(c)
                if any(m[0] == w for m in self.legal):
                    self.sel_w = w
        elif self.sel_dst is None:
            if c in self.s.pos[me]:
                self.sel_w = self.s.pos[me].index(c)
            else:
                opts = [m for m in self.legal if m[0] == self.sel_w and m[1] == c]
                if opts:
                    if opts[0][2] == -1:
                        return self.play(opts[0])
                    self.sel_dst = c
        else:
            m = (self.sel_w, self.sel_dst, c)
            if m in self.legal:
                return self.play(m)
            self.sel_dst = None
            if c in self.s.pos[me]:
                self.sel_w = self.s.pos[me].index(c)
        self.draw()

    def play(self, m):
        self.last = (self.s.pos[self.s.turn][m[0]], m[1], m[2])
        self.s.make(m)
        self.sel_w = self.sel_dst = None
        self.after_move()

    def after_move(self):
        self.legal = self.s.moves() if self.s.winner == -1 else []
        self.draw()
        if self.s.winner == -1 and self.legal and self.s.turn != self.human:
            self.ai_turn()

    def ai_turn(self):
        self.busy = True
        self.draw()
        snap, gen = self.s.copy(), self.gen

        def work():
            m = self.ai.choose(snap)
            self.root.after(0, lambda: self.apply_ai(m, gen))
        threading.Thread(target=work, daemon=True).start()

    def apply_ai(self, m, gen):
        if gen != self.gen:
            return
        self.busy = False
        self.play(m)

    # ---- drawing ------------------------------------------------------
    def draw(self):
        cv, s = self.canvas, self.s
        cv.delete("all")
        hl_dst, hl_b = set(), set()
        if self.s.turn == self.human and not self.busy:
            if self.sel_w is not None and self.sel_dst is None:
                hl_dst = {m[1] for m in self.legal if m[0] == self.sel_w}
            elif self.sel_dst is not None:
                hl_b = {m[2] for m in self.legal if m[0] == self.sel_w and m[1] == self.sel_dst}
        for i in range(N * N):
            r, c = divmod(i, N)
            x0, y0 = c * CELL, r * CELL
            lvl = s.h[i]
            cv.create_rectangle(x0, y0, x0 + CELL, y0 + CELL, fill=COLORS[min(lvl, 3)] if lvl < 4 else COLORS[3], outline="#555")
            for k in range(1, min(lvl, 3) + 1):          # nested squares = levels
                p = 8 * k
                cv.create_rectangle(x0 + p, y0 + p, x0 + CELL - p, y0 + CELL - p, fill=COLORS[k], outline="#456")
            if lvl == 4:
                cv.create_oval(x0 + 22, y0 + 22, x0 + CELL - 22, y0 + CELL - 22, fill="#1e3a8a", outline="white", width=2)
            cv.create_text(x0 + 8, y0 + 8, text=cell_name(i), anchor="nw", fill="#333", font=("Arial", 8))
            if lvl < 4:
                cv.create_text(x0 + CELL - 8, y0 + 8, text=str(lvl), anchor="ne", fill="#222", font=("Arial", 10, "bold"))
            if i in hl_dst or i in hl_b:
                col = "#22c55e" if i in hl_dst else "#f59e0b"
                cv.create_rectangle(x0 + 3, y0 + 3, x0 + CELL - 3, y0 + CELL - 3, outline=col, width=4)
            if s.occ[i] != -1:
                p = s.occ[i]
                sel = p == self.human and self.sel_w is not None and s.pos[p][self.sel_w] == i
                cv.create_oval(x0 + 28, y0 + 28, x0 + CELL - 28, y0 + CELL - 28, fill=WORKER[p],
                               outline="black" if not sel else "#facc15", width=4 if sel else 1)
        if self.last:
            for i in self.last[:2]:
                r, c = divmod(i, N)
                cv.create_rectangle(c * CELL + 1, r * CELL + 1, (c + 1) * CELL - 1, (r + 1) * CELL - 1, outline="#a855f7", dash=(4, 3), width=2)
        you = "red" if self.human == 0 else "blue"
        if s.winner != -1:
            msg = "You win!" if s.winner == self.human else "AI wins."
        elif not self.legal:
            msg = ("AI is stuck - you win!" if s.turn != self.human else "You have no moves - AI wins.")
        elif self.busy:
            msg = f"AI thinking... (you are {you})"
        elif self.sel_w is None:
            msg = f"Your move ({you}): select a worker"
        elif self.sel_dst is None:
            msg = "Click a green cell to move"
        else:
            msg = "Click an orange cell to build"
        self.status.config(text=msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", type=float, default=1.0)
    ap.add_argument("--ai-first", action="store_true")
    a = ap.parse_args()
    root = tk.Tk(); root.title("Santorini")
    App(root, a.time, a.ai_first)
    root.mainloop()


if __name__ == "__main__":
    main()
