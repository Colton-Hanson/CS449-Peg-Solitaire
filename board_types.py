"""
english_board.py - Board shape definitions for Peg Solitaire.
"""

from board import Board, PEG, EMPTY, INVALID


class EnglishBoard(Board):
    """Classic English cross/plus shape. Corners cut off."""
    def _build_grid(self):
        n = self.size
        arm = n // 3
        center = n // 2
        self.grid = []
        for r in range(n):
            row = []
            for c in range(n):
                if (r < arm or r >= n - arm) and (c < arm or c >= n - arm):
                    row.append(INVALID)
                elif r == center and c == center:
                    row.append(EMPTY)
                else:
                    row.append(PEG)
            self.grid.append(row)


class HexagonBoard(Board):
    """
    Hexagon shape — flat top and bottom like a real hex board.
    Top/bottom rows are n//2 wide, middle row is full width.
    Looks like: wider flat rows at top/bottom, not pointy.

    For size=7:
      row 0: 4 wide  (pad=1 each side... but from n//3 start)
      row 3: 7 wide  (full)
    """
    def _build_grid(self):
        n = self.size
        center = n // 2
        # Hexagon: top and bottom rows start at n//3 width, grow to n
        # We divide the grid into thirds vertically
        third = n // 3
        self.grid = []
        for r in range(n):
            dist = abs(r - center)
            # Outer third rows are cut on sides like English but less
            if dist >= third:
                pad = dist - third + 1
            else:
                pad = 0
            row = []
            for c in range(n):
                if c < pad or c >= n - pad:
                    row.append(INVALID)
                elif r == center and c == center:
                    row.append(EMPTY)
                else:
                    row.append(PEG)
            self.grid.append(row)


class DiamondBoard(Board):
    """
    Diamond shape — pointy on all 4 sides, Manhattan distance.
    Single peg at top, widens to center, narrows to single peg at bottom.
    """
    def _build_grid(self):
        n = self.size
        center = n // 2
        radius = center
        self.grid = []
        for r in range(n):
            row = []
            for c in range(n):
                dist = abs(r - center) + abs(c - center)
                if dist > radius:
                    row.append(INVALID)
                elif r == center and c == center:
                    row.append(EMPTY)
                else:
                    row.append(PEG)
            self.grid.append(row)


def create_board(board_type, size):
    board_type = board_type.lower()
    if board_type == "english":
        return EnglishBoard(size)
    elif board_type == "hexagon":
        return HexagonBoard(size)
    elif board_type == "diamond":
        return DiamondBoard(size)
    else:
        raise ValueError(f"Unknown board type: {board_type}")
