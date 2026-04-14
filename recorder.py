"""
recorder.py - Game recording and replay for Peg Solitaire.
Handles saving game sessions to a text file and replaying them.

File format:
    BOARD_TYPE=English
    BOARD_SIZE=7
    MODE=Manual
    MOVE fr fc tr tc
    RANDOMIZE r,c,val r,c,val ...   (space-separated cell changes)
"""


class GameRecorder:
    """Records moves and board states to a text file."""

    def __init__(self, board_type, board_size, mode):
        self.board_type = board_type
        self.board_size = board_size
        self.mode = mode
        self._events = []

    def record_move(self, from_row, from_col, to_row, to_col):
        """Log a single move."""
        self._events.append(f"MOVE {from_row} {from_col} {to_row} {to_col}")

    def record_randomize(self, grid):
        """
        Log the full board state after a randomize.
        grid is a list of lists (rows) containing cell values.
        """
        cells = []
        for r, row in enumerate(grid):
            for c, val in enumerate(row):
                cells.append(f"{r},{c},{val}")
        self._events.append("RANDOMIZE " + " ".join(cells))

    def save(self, filepath):
        """Write the recorded session to a file."""
        with open(filepath, "w") as f:
            f.write(f"BOARD_TYPE={self.board_type}\n")
            f.write(f"BOARD_SIZE={self.board_size}\n")
            f.write(f"MODE={self.mode}\n")
            for event in self._events:
                f.write(event + "\n")


class GameReplayer:
    """Loads a recorded session and steps through it."""

    def __init__(self, filepath):
        self.board_type = None
        self.board_size = None
        self.mode = None
        self.events = []
        self._load(filepath)
        self._index = 0

    def _load(self, filepath):
        with open(filepath, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            if line.startswith("BOARD_TYPE="):
                self.board_type = line.split("=", 1)[1]
            elif line.startswith("BOARD_SIZE="):
                self.board_size = int(line.split("=", 1)[1])
            elif line.startswith("MODE="):
                self.mode = line.split("=", 1)[1]
            elif line.startswith("MOVE "):
                parts = line.split()
                fr, fc, tr, tc = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                self.events.append(("MOVE", fr, fc, tr, tc))
            elif line.startswith("RANDOMIZE "):
                cells = []
                tokens = line.split()[1:]
                for token in tokens:
                    r, c, val = token.split(",")
                    cells.append((int(r), int(c), int(val)))
                self.events.append(("RANDOMIZE", cells))

    def has_next(self):
        return self._index < len(self.events)

    def next_event(self):
        """Return the next event and advance the index."""
        if not self.has_next():
            return None
        event = self.events[self._index]
        self._index += 1
        return event

    def reset(self):
        self._index = 0