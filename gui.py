"""
gui.py - Tkinter GUI for Peg Solitaire.
All display and user interaction lives here.
Game logic is handled entirely by board.py / board_types.py / game.py.
"""

import tkinter as tk
from tkinter import messagebox
import random
from board_types import create_board
from board import PEG, EMPTY, INVALID
from game import ManualGame, AutomatedGame

CELL_SIZE = 50
PEG_RADIUS = 18
COLORS = {
    "bg": "#2b2b2b",              # dark sidebar
    "board_bg": "#ffffff",        # white board canvas
    "cell_empty": "#cccccc",      # light gray empty hole
    "peg": "#1a1a1a",             # black peg
    "peg_selected": "#ff6b35",    # orange selected
    "peg_valid_dest": "#7ec850",  # green valid destination
    "invalid": "#ffffff",
    "text": "#f0e6d3",            # warm light text
    "button": "#5c4033",          # dark brown button
    "button_text": "#f0e6d3",
}


class SolitaireGUI:
    """Main application window. Owns the game model and all widgets."""

    def __init__(self, root):
        self.root = root
        self.root.title("Peg Solitaire")
        self.root.configure(bg=COLORS["bg"])
        self.board = None        # current Board (preview or active game)
        self.game = None         # current Game instance (None during preview)
        self.preview_mode = True
        self._autoplay_job = None  # pending after() id for autoplay timer

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
                command=self._preview_board
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

        # Game Mode
        tk.Label(ctrl, text="\nGame Mode", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 12, "bold")).pack(anchor="w")

        self.game_mode_var = tk.StringVar(value="Manual")
        for mode in ["Manual", "Autoplay"]:
            tk.Radiobutton(
                ctrl, text=mode, variable=self.game_mode_var,
                value=mode, bg=COLORS["bg"], fg=COLORS["text"],
                selectcolor=COLORS["button"], activebackground=COLORS["bg"],
                font=("Helvetica", 11)
            ).pack(anchor="w")

        # New Game button
        tk.Button(ctrl, text="New Game", command=self._new_game,
                  bg=COLORS["button"], fg=COLORS["button_text"],
                  font=("Helvetica", 12, "bold"), relief="flat",
                  padx=10, pady=6).pack(pady=(20, 0), fill="x")

        # Autoplay button (starts/stops autoplay on the current game)
        self.autoplay_btn = tk.Button(
            ctrl, text="Autoplay", command=self._toggle_autoplay,
            bg=COLORS["button"], fg=COLORS["button_text"],
            font=("Helvetica", 11), relief="flat", padx=10, pady=4
        )
        self.autoplay_btn.pack(pady=(8, 0), fill="x")

        # Randomize button
        tk.Button(ctrl, text="Randomize", command=self._randomize,
                  bg=COLORS["button"], fg=COLORS["button_text"],
                  font=("Helvetica", 11), relief="flat",
                  padx=10, pady=4).pack(pady=(8, 0), fill="x")

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
        self._stop_autoplay()
        self.game = None
        self.board = create_board(board_type, size)
        self.preview_mode = True

        self._resize_canvas()
        self._draw_board()
        self.status_var.set(f"Preview: {board_type} board, size {size}. Click New Game to play.")

    # ── New Game ───────────────────────────────────────────────────────────

    def _new_game(self):
        """Validate inputs, start a fresh game in the selected mode."""
        try:
            size = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("Invalid Size", "Board size must be a number.")
            return

        if size < 5 or size > 11 or size % 2 == 0:
            messagebox.showerror("Invalid Size",
                                 "Board size must be an odd number between 5 and 11.")
            return

        self._stop_autoplay()

        board_type = self.board_type_var.get()
        board = create_board(board_type, size)

        if self.game_mode_var.get() == "Autoplay":
            self.game = AutomatedGame(board)
        else:
            self.game = ManualGame(board)

        self.board = self.game.board
        self.preview_mode = False

        self._resize_canvas()
        self._draw_board()
        self.status_var.set(
            f"{board_type} board, size {size}. Pegs: {self.board.count_pegs()}"
        )

        if isinstance(self.game, AutomatedGame):
            self._start_autoplay()

    def _resize_canvas(self):
        n = self.board.size
        canvas_size = n * CELL_SIZE + 20
        self.canvas.config(width=canvas_size, height=canvas_size)

    # ── Autoplay ───────────────────────────────────────────────────────────

    def _toggle_autoplay(self):
        """Start autoplay if stopped; stop it if running."""
        if self._autoplay_job is not None:
            self._stop_autoplay()
            self.status_var.set("Autoplay paused.")
            return

        if self.board is None or self.preview_mode:
            return

        # Switch current game to AutomatedGame if it isn't already
        if not isinstance(self.game, AutomatedGame):
            self.game = AutomatedGame(self.board)

        if not self.game.is_game_over():
            self._start_autoplay()

    def _start_autoplay(self):
        self.autoplay_btn.config(text="Stop")
        self._autoplay_step()

    def _stop_autoplay(self):
        if self._autoplay_job is not None:
            self.root.after_cancel(self._autoplay_job)
            self._autoplay_job = None
        self.autoplay_btn.config(text="Autoplay")

    def _autoplay_step(self):
        """Called every 300 ms while autoplay is running."""
        self._autoplay_job = None  # clear before potentially setting a new one

        if self.game is None or not isinstance(self.game, AutomatedGame):
            return

        move = self.game.play_random_move()
        if move is None or self.game.is_game_over():
            self._draw_board()
            self._stop_autoplay()
            self._check_game_over()
            return

        self._draw_board()
        pegs = self.game.get_pegs()
        self.status_var.set(f"Autoplay: {pegs} pegs remaining")
        self._autoplay_job = self.root.after(300, self._autoplay_step)

    # ── Randomize ──────────────────────────────────────────────────────────

    def _randomize(self):
        """Shuffle pegs into a random valid board state (same peg count)."""
        if self.board is None or self.preview_mode:
            return

        self._stop_autoplay()

        peg_count = self.board.count_pegs()
        valid_cells = [
            (r, c)
            for r in range(self.board.size)
            for c in range(len(self.board.grid[r]))
            if self.board.grid[r][c] != INVALID
        ]

        if peg_count > len(valid_cells) or peg_count == 0:
            return

        # Try up to 200 times to land on a state with at least one valid move.
        for _ in range(200):
            peg_positions = set(random.sample(valid_cells, peg_count))
            for r, c in valid_cells:
                self.board.set_cell(r, c, PEG if (r, c) in peg_positions else EMPTY)
            if self.board.has_valid_moves():
                break

        # Clear any selection state
        if isinstance(self.game, ManualGame):
            self.game.deselect()

        self._draw_board()
        self.status_var.set(f"Board randomized. Pegs: {self.board.count_pegs()}")

    # ── Drawing ────────────────────────────────────────────────────────────

    def _draw_board(self):
        self.canvas.delete("all")
        offset = 10

        # Selection state comes from ManualGame when applicable
        selected = None
        valid_destinations = []
        if isinstance(self.game, ManualGame):
            selected = self.game.selected
            valid_destinations = self.game.valid_destinations

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
                    if selected == (r, c):
                        color = COLORS["peg_selected"]
                    elif (r, c) in valid_destinations:
                        color = COLORS["peg_valid_dest"]
                    else:
                        color = COLORS["peg"]

                    self.canvas.create_oval(
                        x - PEG_RADIUS + 4, y - PEG_RADIUS + 4,
                        x + PEG_RADIUS - 4, y + PEG_RADIUS - 4,
                        fill=color, outline="#000000", width=1,
                        tags=f"peg_{r}_{c}"
                    )

                elif (r, c) in valid_destinations:
                    # Empty destination hole with green dot
                    self.canvas.create_oval(
                        x - PEG_RADIUS + 8, y - PEG_RADIUS + 8,
                        x + PEG_RADIUS - 8, y + PEG_RADIUS - 8,
                        fill=COLORS["peg_valid_dest"], outline="", width=0,
                        tags=f"dest_{r}_{c}"
                    )

    # ── Interaction ────────────────────────────────────────────────────────

    def _on_click(self, event):
        # Only handle clicks during an active ManualGame
        if self.board is None or self.preview_mode:
            return
        if not isinstance(self.game, ManualGame):
            return

        offset = 10
        col = (event.x - offset) // CELL_SIZE
        row = (event.y - offset) // CELL_SIZE

        if row < 0 or row >= self.board.size or col < 0 or col >= self.board.size:
            return

        cell_val = self.board.get_cell(row, col)
        if cell_val == INVALID:
            return

        game = self.game  # ManualGame

        if game.selected is None:
            if cell_val == PEG:
                moves = game.select_peg(row, col)
                if not moves:
                    self.status_var.set("That peg has no valid moves.")
                else:
                    self.status_var.set(f"Peg selected at ({row},{col}). Choose a destination.")
                    self._draw_board()
            return

        # A peg is already selected
        if (row, col) in game.valid_destinations:
            success = game.attempt_move(row, col)
            if success:
                self._draw_board()
                self._check_game_over()
            return

        if cell_val == PEG:
            moves = game.select_peg(row, col)
            if moves:
                self.status_var.set(f"Peg selected at ({row},{col}). Choose a destination.")
                self._draw_board()
                return

        game.deselect()
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
