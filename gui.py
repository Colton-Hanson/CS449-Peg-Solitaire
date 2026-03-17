"""
gui.py - Tkinter GUI for Peg Solitaire.
All display and user interaction lives here.
Game logic is handled entirely by board.py / english_board.py.
"""

import tkinter as tk
from tkinter import messagebox
from board_types import create_board
from board import PEG, EMPTY, INVALID

CELL_SIZE = 50
PEG_RADIUS = 18
COLORS = {
    "bg": "#2b2b2b",           # dark sidebar
    "board_bg": "#ffffff",     # white board canvas
    "cell_empty": "#cccccc",   # light gray empty hole
    "peg": "#1a1a1a",          # black peg
    "peg_selected": "#ff6b35", # orange selected
    "peg_valid_dest": "#7ec850", # green valid destination
    "invalid": "#ffffff",
    "text": "#f0e6d3",         # warm light text
    "button": "#5c4033",       # dark brown button
    "button_text": "#f0e6d3",
}


class SolitaireGUI:
    """Main application window. Owns the board model and all widgets."""

    def __init__(self, root):
        self.root = root
        self.root.title("Peg Solitaire")
        self.root.configure(bg=COLORS["bg"])
        self.board = None
        self.selected = None
        self.valid_destinations = []
        self.preview_mode = True  # True = just previewing shape, not playing

        self._build_controls()
        self._build_canvas()
        self._build_status()

        # Show default preview on launch
        self._preview_board()

    # ── Controls (left panel) ──────────────────────────────────────────────

    def _build_controls(self):
        ctrl = tk.Frame(self.root, bg=COLORS["bg"], padx=12, pady=12)
        ctrl.grid(row=0, column=0, sticky="ns")

        # Board Type
        tk.Label(ctrl, text="Board Type", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 4))

        self.board_type_var = tk.StringVar(value="English")
        for btype in ["English", "Hexagon", "Diamond"]:
            tk.Radiobutton(
                ctrl, text=btype, variable=self.board_type_var,
                value=btype, bg=COLORS["bg"], fg=COLORS["text"],
                selectcolor=COLORS["button"], activebackground=COLORS["bg"],
                font=("Helvetica", 11),
                command=self._preview_board   # ← instantly update on click
            ).pack(anchor="w")

        # Board Size
        tk.Label(ctrl, text="\nBoard Size", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 12, "bold")).pack(anchor="w")

        size_frame = tk.Frame(ctrl, bg=COLORS["bg"])
        size_frame.pack(anchor="w", pady=4)
        self.size_var = tk.StringVar(value="7")
        self.size_var.trace_add("write", lambda *_: self._preview_board())
        tk.Entry(size_frame, textvariable=self.size_var, width=4,
                 font=("Helvetica", 12), justify="center").pack(side="left")
        tk.Label(size_frame, text=" (5–11, odd)", bg=COLORS["bg"],
                 fg=COLORS["text"], font=("Helvetica", 9)).pack(side="left")

        # New Game button
        tk.Button(ctrl, text="New Game", command=self._new_game,
                  bg=COLORS["button"], fg=COLORS["button_text"],
                  font=("Helvetica", 12, "bold"), relief="flat",
                  padx=10, pady=6).pack(pady=(20, 0), fill="x")

    # ── Canvas ─────────────────────────────────────────────────────────────

    def _build_canvas(self):
        self.canvas = tk.Canvas(self.root, bg=COLORS["board_bg"],
                                highlightthickness=0)
        self.canvas.grid(row=0, column=1, padx=12, pady=12)
        self.canvas.bind("<Button-1>", self._on_click)

    def _build_status(self):
        self.status_var = tk.StringVar(value="Choose a board type and click New Game.")
        tk.Label(self.root, textvariable=self.status_var,
                 bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 11)).grid(row=1, column=0, columnspan=2, pady=(0, 10))

    # ── Preview (show shape before game starts) ────────────────────────────

    def _preview_board(self):
        """Show the board shape without starting a game."""
        try:
            size = int(self.size_var.get())
        except ValueError:
            return
        if size < 5 or size > 11 or size % 2 == 0:
            return

        board_type = self.board_type_var.get()
        self.board = create_board(board_type, size)
        self.selected = None
        self.valid_destinations = []
        self.preview_mode = True

        self._resize_canvas()
        self._draw_board()
        self.status_var.set(f"Preview: {board_type} board, size {size}. Click New Game to play.")

    # ── New Game ───────────────────────────────────────────────────────────

    def _new_game(self):
        """Validate inputs, start a fresh playable game."""
        try:
            size = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("Invalid Size", "Board size must be a number.")
            return

        if size < 5 or size > 11 or size % 2 == 0:
            messagebox.showerror("Invalid Size",
                                 "Board size must be an odd number between 5 and 11.")
            return

        board_type = self.board_type_var.get()
        self.board = create_board(board_type, size)
        self.selected = None
        self.valid_destinations = []
        self.preview_mode = False

        self._resize_canvas()
        self._draw_board()
        self.status_var.set(f"{board_type} board, size {size}. Pegs: {self.board.count_pegs()}")

    def _resize_canvas(self):
        n = self.board.size
        canvas_size = n * CELL_SIZE + 20
        self.canvas.config(width=canvas_size, height=canvas_size)

    # ── Drawing ────────────────────────────────────────────────────────────

    def _draw_board(self):
        self.canvas.delete("all")
        offset = 10

        for r in range(self.board.size):
            for c in range(len(self.board.grid[r])):
                val = self.board.grid[r][c]
                if val == INVALID:
                    continue

                x = offset + c * CELL_SIZE + CELL_SIZE // 2
                y = offset + r * CELL_SIZE + CELL_SIZE // 2

                # Draw hole
                self.canvas.create_oval(
                    x - PEG_RADIUS, y - PEG_RADIUS,
                    x + PEG_RADIUS, y + PEG_RADIUS,
                    fill=COLORS["cell_empty"], outline="#999999", width=1,
                    tags=f"cell_{r}_{c}"
                )

                if val == PEG:
                    if self.selected == (r, c):
                        color = COLORS["peg_selected"]
                    elif (r, c) in self.valid_destinations:
                        color = COLORS["peg_valid_dest"]
                    else:
                        color = COLORS["peg"]

                    self.canvas.create_oval(
                        x - PEG_RADIUS + 4, y - PEG_RADIUS + 4,
                        x + PEG_RADIUS - 4, y + PEG_RADIUS - 4,
                        fill=color, outline="#000000", width=1,
                        tags=f"peg_{r}_{c}"
                    )

                elif (r, c) in self.valid_destinations:
                    self.canvas.create_oval(
                        x - PEG_RADIUS + 8, y - PEG_RADIUS + 8,
                        x + PEG_RADIUS - 8, y + PEG_RADIUS - 8,
                        fill=COLORS["peg_valid_dest"], outline="", width=0,
                        tags=f"dest_{r}_{c}"
                    )

    # ── Interaction ────────────────────────────────────────────────────────

    def _on_click(self, event):
        # Don't allow moves during preview
        if self.board is None or self.preview_mode:
            return

        offset = 10
        col = (event.x - offset) // CELL_SIZE
        row = (event.y - offset) // CELL_SIZE

        if row < 0 or row >= self.board.size or col < 0 or col >= self.board.size:
            return

        cell_val = self.board.get_cell(row, col)
        if cell_val == INVALID:
            return

        if self.selected is None:
            if cell_val == PEG:
                moves = self.board.get_valid_moves_from(row, col)
                if not moves:
                    self.status_var.set("That peg has no valid moves.")
                    return
                self.selected = (row, col)
                self.valid_destinations = moves
                self.status_var.set(f"Peg selected at ({row},{col}). Choose a destination.")
                self._draw_board()
            return

        from_row, from_col = self.selected

        if (row, col) in self.valid_destinations:
            success = self.board.make_move(from_row, from_col, row, col)
            self.selected = None
            self.valid_destinations = []
            if success:
                self._draw_board()
                self._check_game_over()
            return

        if cell_val == PEG:
            moves = self.board.get_valid_moves_from(row, col)
            if moves:
                self.selected = (row, col)
                self.valid_destinations = moves
                self.status_var.set(f"Peg selected at ({row},{col}). Choose a destination.")
                self._draw_board()
                return

        self.selected = None
        self.valid_destinations = []
        self.status_var.set("Deselected. Click a peg to begin.")
        self._draw_board()

    def _check_game_over(self):
        pegs = self.board.count_pegs()
        self.status_var.set(f"Pegs remaining: {pegs}")
        if self.board.is_game_over():
            rating = self.board.get_rating()
            messagebox.showinfo("Game Over",
                                f"Game over!\nPegs remaining: {pegs}\nRating: {rating}")
            self.status_var.set(f"Game over! Rating: {rating} ({pegs} pegs left)")


def main():
    root = tk.Tk()
    app = SolitaireGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
