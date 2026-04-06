"""
game.py - Game session classes for Peg Solitaire.
Separates session/interaction logic from raw board state (board.py).

Class hierarchy:
    Game            -- shared logic (move counting, all-valid-moves, game-over)
    ManualGame      -- click-driven; owns selection state
    AutomatedGame   -- plays random valid moves programmatically
"""

import random
from board import PEG


class Game:
    """Base class: wraps a Board and tracks move count."""

    def __init__(self, board):
        self.board = board
        self.move_count = 0

    def get_all_valid_moves(self):
        """Return every legal move as a list of (from_row, from_col, to_row, to_col)."""
        moves = []
        for r in range(len(self.board.grid)):
            for c in range(len(self.board.grid[r])):
                if self.board.grid[r][c] == PEG:
                    for tr, tc in self.board.get_valid_moves_from(r, c):
                        moves.append((r, c, tr, tc))
        return moves

    def make_move(self, from_row, from_col, to_row, to_col):
        """Execute a move; returns True on success."""
        result = self.board.make_move(from_row, from_col, to_row, to_col)
        if result:
            self.move_count += 1
        return result

    def is_game_over(self):
        return self.board.is_game_over()

    def get_pegs(self):
        return self.board.count_pegs()

    def get_rating(self):
        return self.board.get_rating()


class ManualGame(Game):
    """Human-driven game. Tracks which peg is selected and its valid destinations."""

    def __init__(self, board):
        super().__init__(board)
        self.selected = None          # (row, col) of selected peg, or None
        self.valid_destinations = []  # list of (row, col) the selected peg can reach

    def select_peg(self, row, col):
        """
        Try to select the peg at (row, col).
        Returns the list of valid destination cells, or [] if the cell has none.
        """
        moves = self.board.get_valid_moves_from(row, col)
        if moves:
            self.selected = (row, col)
            self.valid_destinations = moves
        return moves

    def deselect(self):
        """Clear the current selection."""
        self.selected = None
        self.valid_destinations = []

    def attempt_move(self, to_row, to_col):
        """
        Move the currently selected peg to (to_row, to_col).
        Clears selection regardless of outcome; returns True on success.
        """
        if self.selected is None:
            return False
        from_row, from_col = self.selected
        self.deselect()
        return self.make_move(from_row, from_col, to_row, to_col)


class AutomatedGame(Game):
    """Plays the game automatically by choosing random valid moves."""

    def __init__(self, board):
        super().__init__(board)

    def play_random_move(self):
        """
        Pick and execute one random valid move.
        Returns (from_row, from_col, to_row, to_col) on success, or None if game over.
        """
        moves = self.get_all_valid_moves()
        if not moves:
            return None
        move = random.choice(moves)
        self.make_move(*move)
        return move

    def play_to_end(self):
        """Play random moves until no moves remain. Returns total moves played."""
        while not self.is_game_over():
            if self.play_random_move() is None:
                break
        return self.move_count
