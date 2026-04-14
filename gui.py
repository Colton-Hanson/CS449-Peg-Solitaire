"""
gui.py - Tkinter GUI for Peg Solitaire.
All display and user interaction lives here.
Game logic is handled entirely by board.py / board_types.py / game.py.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import random
from board_types import create_board
from board import PEG, EMPTY, INVALID
from game import ManualGame, AutomatedGame
from recorder import GameRecorder, GameReplayer

CELL_SIZE = 50
PEG_RADIUS = 18
COLORS = {
    "bg": "#2b2b2b",
    "board_bg": "#ffffff",
    "cell_empty": "#cccccc",
    "peg": "#1a1a1a",
    "peg_selected": "#ff6b35",
    "peg_valid_dest": "#7ec850",
    "invalid": "#ffffff",
    "text": "#f0e6d3",
    "button": "#5c4033",
    "button_text": "#f0e6d3",
}


class SolitaireGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Peg Solitaire")
        self.root.configure(bg=COLORS["bg"])
        self.board = None
        self.game = None
        self.preview_mode = True
        self._autoplay_job = None
        self.recorder = None
        self.record_var = tk.BooleanVar(value=False)
        self._replay_job = None
        self._replayer = None

        self._build_controls()
        self._build_canvas()
        self._build_status()
        self._preview_board()

    def _build_controls(self):
        ctrl = tk.Frame(self.root, bg=COLORS["bg"], padx=12, pady=12)
        ctrl.grid(row=0, column=0, sticky="ns")

        tk.Label(ctrl, text="Board Type", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 4))

        self.board_type_var = tk.StringVar(value="English")
        for btype in ["English", "Hexagon", "Diamond"]:
            tk.Radiobutton(
                ctrl, text=btype, variable=self.board_type_var,
                value=btype, bg=COLORS["bg"], fg=COLORS["text"],
                selectcolor=COLORS["button"], activebackground=COLORS["bg"],
                font=("Helvetica", 11), command=self._preview_board
            ).pack(anchor="w")

        tk.Label(ctrl, text="\nBoard Size", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 12, "bold")).pack(anchor="w")

        size_frame = tk.Frame(ctrl, bg=COLORS["bg"])
        size_frame.pack(anchor="w", pady=4)
        self.size_var = tk.StringVar(value="7")
        self.size_var.trace_add("write", lambda *_: self._preview_board())
        tk.Entry(size_frame, textvariable=self.size_var, width=4,
                 font=("Helvetica", 12), justify="center").pack(side="left")
        tk.Label(size_frame, text=" (5-11, odd)", bg=COLORS["bg"],
                 fg=COLORS["text"], font=("Helvetica", 9)).pack(side="left")

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

        tk.Label(ctrl, text="", bg=COLORS["bg"]).pack()
        tk.Checkbutton(
            ctrl, text="Record Game", variable=self.record_var,
            bg=COLORS["bg"], fg=COLORS["text"],
            selectcolor=COLORS["button"], activebackground=COLORS["bg"],
            font=("Helvetica", 11)
        ).pack(anchor="w")

        tk.Button(ctrl, text="New Game", command=self._new_game,
                  bg=COLORS["button"], fg=COLORS["button_text"],
                  font=("Helvetica", 12, "bold"), relief="flat",
                  padx=10, pady=6).pack(pady=(12, 0), fill="x")

        tk.Button(ctrl, text="Replay", command=self._start_replay,
                  bg=COLORS["button"], fg=COLORS["button_text"],
                  font=("Helvetica", 11), relief="flat",
                  padx=10, pady=4).pack(pady=(8, 0), fill="x")

        self.autoplay_btn = tk.Button(
            ctrl, text="Autoplay", command=self._toggle_autoplay,
            bg=COLORS["button"], fg=COLORS["button_text"],
            font=("Helvetica", 11), relief="flat", padx=10, pady=4
        )
        self.autoplay_btn.pack(pady=(8, 0), fill="x")

        tk.Button(ctrl, text="Randomize", command=self._randomize,
                  bg=COLORS["button"], fg=COLORS["button_text"],
                  font=("Helvetica", 11), relief="flat",
                  padx=10, pady=4).pack(pady=(8, 0), fill="x")

    def _build_canvas(self):
        self.canvas = tk.Canvas(self.root, bg=COLORS["board_bg"], highlightthickness=0)
        self.canvas.grid(row=0, column=1, padx=12, pady=12)
        self.canvas.bind("<Button-1>", self._on_click)

    def _build_status(self):
        self.status_var = tk.StringVar(value="Choose a board type and click New Game.")
        tk.Label(self.root, textvariable=self.status_var,
                 bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 11)).grid(row=1, column=0, columnspan=2, pady=(0, 10))

    def _preview_board(self):
        try:
            size = int(self.size_var.get())
        except ValueError:
            return
        if size < 5 or size > 11 or size % 2 == 0:
            return
        board_type = self.board_type_var.get()
        self._stop_autoplay()
        self._stop_replay()
        self.game = None
        self.board = create_board(board_type, size)
        self.preview_mode = True
        self._resize_canvas()
        self._draw_board()
        self.status_var.set(f"Preview: {board_type} board, size {size}. Click New Game to play.")

    def _new_game(self):
        try:
            size = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("Invalid Size", "Board size must be a number.")
            return
        if size < 5 or size > 11 or size % 2 == 0:
            messagebox.showerror("Invalid Size", "Board size must be an odd number between 5 and 11.")
            return

        self._stop_autoplay()
        self._stop_replay()

        board_type = self.board_type_var.get()
        mode = self.game_mode_var.get()
        board = create_board(board_type, size)

        if mode == "Autoplay":
            self.game = AutomatedGame(board)
        else:
            self.game = ManualGame(board)

        self.board = self.game.board
        self.preview_mode = False

        if self.record_var.get():
            self.recorder = GameRecorder(board_type, size, mode)
        else:
            self.recorder = None

        self._resize_canvas()
        self._draw_board()
        rec_label = " | Recording..." if self.recorder else ""
        self.status_var.set(f"{board_type} board, size {size}. Pegs: {self.board.count_pegs()}{rec_label}")

        if isinstance(self.game, AutomatedGame):
            self._start_autoplay()

    def _resize_canvas(self):
        n = self.board.size
        canvas_size = n * CELL_SIZE + 20
        self.canvas.config(width=canvas_size, height=canvas_size)

    def _toggle_autoplay(self):
        if self._autoplay_job is not None:
            self._stop_autoplay()
            self.status_var.set("Autoplay paused.")
            return
        if self.board is None or self.preview_mode:
            return
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
        self._autoplay_job = None
        if self.game is None or not isinstance(self.game, AutomatedGame):
            return
        move = self.game.play_random_move()
        if move is None or self.game.is_game_over():
            if move and self.recorder:
                self.recorder.record_move(*move)
            self._draw_board()
            self._stop_autoplay()
            self._finish_recording()
            self._check_game_over()
            return
        if self.recorder:
            self.recorder.record_move(*move)
        self._draw_board()
        pegs = self.game.get_pegs()
        rec_label = " | Recording..." if self.recorder else ""
        self.status_var.set(f"Autoplay: {pegs} pegs remaining{rec_label}")
        self._autoplay_job = self.root.after(300, self._autoplay_step)

    def _randomize(self):
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
        for _ in range(200):
            peg_positions = set(random.sample(valid_cells, peg_count))
            for r, c in valid_cells:
                self.board.set_cell(r, c, PEG if (r, c) in peg_positions else EMPTY)
            if self.board.has_valid_moves():
                break
        if isinstance(self.game, ManualGame):
            self.game.deselect()
        if self.recorder:
            self.recorder.record_randomize(self.board.grid)
        self._draw_board()
        rec_label = " | Recording..." if self.recorder else ""
        self.status_var.set(f"Board randomized. Pegs: {self.board.count_pegs()}{rec_label}")

    def _finish_recording(self):
        if self.recorder is None:
            return
        filepath = filedialog.asksaveasfilename(
            title="Save Game Recording",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.recorder.save(filepath)
            self.status_var.set(f"Game saved to {filepath}")
        self.recorder = None

    def _start_replay(self):
        filepath = filedialog.askopenfilename(
            title="Open Game Recording",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return
        self._stop_autoplay()
        self._stop_replay()
        try:
            self._replayer = GameReplayer(filepath)
        except Exception as e:
            messagebox.showerror("Replay Error", f"Could not load file:\n{e}")
            return
        board = create_board(self._replayer.board_type, self._replayer.board_size)
        if self._replayer.mode == "Autoplay":
            self.game = AutomatedGame(board)
        else:
            self.game = ManualGame(board)
        self.board = self.game.board
        self.preview_mode = False
        self.recorder = None
        # Save replayer before setting GUI vars — size_var trace fires _preview_board
        # which calls _stop_replay and would wipe self._replayer to None
        saved_replayer = self._replayer
        self.board_type_var.set(saved_replayer.board_type)
        self.size_var.set(str(saved_replayer.board_size))
        self.game_mode_var.set(saved_replayer.mode)
        self._replayer = saved_replayer  # restore after trace fires
        self._resize_canvas()
        self._draw_board()
        self.status_var.set("Replaying game...")
        self._replay_step()

    def _replay_step(self):
        self._replay_job = None
        if self._replayer is None or not self._replayer.has_next():
            self._stop_replay()
            pegs = self.board.count_pegs()
            rating = self.board.get_rating()
            self.status_var.set(f"Replay complete! Pegs: {pegs} | Rating: {rating}")
            return
        event = self._replayer.next_event()
        if event[0] == "MOVE":
            _, fr, fc, tr, tc = event
            self.board.make_move(fr, fc, tr, tc)
            if isinstance(self.game, ManualGame):
                self.game.deselect()
        elif event[0] == "RANDOMIZE":
            _, cells = event
            for r, c, val in cells:
                self.board.set_cell(r, c, val)
            if isinstance(self.game, ManualGame):
                self.game.deselect()
        self._draw_board()
        pegs = self.board.count_pegs()
        self.status_var.set(f"Replaying... Pegs: {pegs}")
        self._replay_job = self.root.after(400, self._replay_step)

    def _stop_replay(self):
        if self._replay_job is not None:
            self.root.after_cancel(self._replay_job)
            self._replay_job = None
        self._replayer = None

    def _draw_board(self):
        self.canvas.delete("all")
        offset = 10
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
                    self.canvas.create_oval(
                        x - PEG_RADIUS + 8, y - PEG_RADIUS + 8,
                        x + PEG_RADIUS - 8, y + PEG_RADIUS - 8,
                        fill=COLORS["peg_valid_dest"], outline="", width=0,
                        tags=f"dest_{r}_{c}"
                    )

    def _on_click(self, event):
        if self.board is None or self.preview_mode:
            return
        if not isinstance(self.game, ManualGame):
            return
        if self._replayer is not None:
            return
        offset = 10
        col = (event.x - offset) // CELL_SIZE
        row = (event.y - offset) // CELL_SIZE
        if row < 0 or row >= self.board.size or col < 0 or col >= self.board.size:
            return
        cell_val = self.board.get_cell(row, col)
        if cell_val == INVALID:
            return
        game = self.game
        if game.selected is None:
            if cell_val == PEG:
                moves = game.select_peg(row, col)
                if not moves:
                    self.status_var.set("That peg has no valid moves.")
                else:
                    self.status_var.set(f"Peg selected at ({row},{col}). Choose a destination.")
                    self._draw_board()
            return
        if (row, col) in game.valid_destinations:
            from_row, from_col = game.selected
            success = game.attempt_move(row, col)
            if success:
                if self.recorder:
                    self.recorder.record_move(from_row, from_col, row, col)
                self._draw_board()
                if self.board.is_game_over():
                    self._finish_recording()
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