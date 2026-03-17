"""
board.py - Game logic for Peg Solitaire (no UI code here)
Separation of concerns: this file knows nothing about Tkinter or display.
"""

EMPTY = 0
PEG = 1
INVALID = -1  # cells that are off-board for a given shape


class Board:
    """
    Base class representing the Peg Solitaire board state and rules.
    Subclasses override _build_grid() to define different board shapes.
    """

    def __init__(self, size=7):
        self.size = size
        self.grid = []
        self.selected = None  # (row, col) of currently selected peg
        self._build_grid()

    def _build_grid(self):
        """Override in subclasses to define board shape."""
        raise NotImplementedError("Subclasses must implement _build_grid()")

    def get_cell(self, row, col):
        """Return the value at (row, col), or INVALID if out of bounds."""
        if 0 <= row < len(self.grid) and 0 <= col < len(self.grid[row]):
            return self.grid[row][col]
        return INVALID

    def set_cell(self, row, col, value):
        """Set the value at (row, col)."""
        self.grid[row][col] = value

    def is_valid_move(self, from_row, from_col, to_row, to_col):
        """
        Check if jumping from (from_row, from_col) to (to_row, to_col) is legal.
        The move must be orthogonal, exactly 2 steps, over a peg, into an empty hole.
        """
        # Source must have a peg
        if self.get_cell(from_row, from_col) != PEG:
            return False

        # Destination must be empty and on the board
        if self.get_cell(to_row, to_col) != EMPTY:
            return False

        # Must move exactly 2 in one direction (orthogonal only)
        dr = to_row - from_row
        dc = to_col - from_col
        if (abs(dr) == 2 and dc == 0) or (dr == 0 and abs(dc) == 2):
            mid_row = from_row + dr // 2
            mid_col = from_col + dc // 2
            # The peg being jumped over must exist
            if self.get_cell(mid_row, mid_col) == PEG:
                return True

        return False

    def make_move(self, from_row, from_col, to_row, to_col):
        """
        Execute a move. Returns True if successful, False if invalid.
        """
        if not self.is_valid_move(from_row, from_col, to_row, to_col):
            return False

        dr = to_row - from_row
        dc = to_col - from_col
        mid_row = from_row + dr // 2
        mid_col = from_col + dc // 2

        self.set_cell(from_row, from_col, EMPTY)   # peg leaves
        self.set_cell(mid_row, mid_col, EMPTY)      # jumped peg removed
        self.set_cell(to_row, to_col, PEG)          # peg lands
        self.selected = None
        return True

    def get_valid_moves_from(self, row, col):
        """Return list of valid destination (row, col) tuples for a peg at (row, col)."""
        moves = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            tr, tc = row + dr, col + dc
            if self.is_valid_move(row, col, tr, tc):
                moves.append((tr, tc))
        return moves

    def has_valid_moves(self):
        """Return True if any peg on the board has at least one valid move."""
        for r in range(len(self.grid)):
            for c in range(len(self.grid[r])):
                if self.grid[r][c] == PEG:
                    if self.get_valid_moves_from(r, c):
                        return True
        return False

    def count_pegs(self):
        """Return the total number of pegs remaining on the board."""
        return sum(cell == PEG for row in self.grid for cell in row)

    def is_game_over(self):
        """Return True if the game has ended (no valid moves left)."""
        return not self.has_valid_moves()

    def get_rating(self):
        """Return a rating string based on pegs remaining."""
        pegs = self.count_pegs()
        if pegs == 1:
            return "Outstanding"
        elif pegs == 2:
            return "Very Good"
        elif pegs == 3:
            return "Good"
        else:
            return "Average"
