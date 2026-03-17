"""
test_board.py - pytest unit tests for Peg Solitaire game logic.
Tests cover board initialization, move validation, move execution, and game-over detection.
UI code (gui.py) is NOT imported here — pure logic tests only.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from board import Board, PEG, EMPTY, INVALID
from board_types import EnglishBoard, HexagonBoard, DiamondBoard, create_board


# ── Board Initialization ───────────────────────────────────────────────────

class TestEnglishBoardInit:

    def test_default_size_is_7(self):
        board = EnglishBoard()
        assert board.size == 7

    def test_custom_size(self):
        board = EnglishBoard(5)
        assert board.size == 5

    def test_center_is_empty(self):
        board = EnglishBoard(7)
        center = 7 // 2  # = 3
        assert board.get_cell(center, center) == EMPTY

    def test_non_center_valid_cell_has_peg(self):
        board = EnglishBoard(7)
        # (3, 0) is a valid cell on the English board but not the center
        assert board.get_cell(3, 0) == PEG

    def test_corner_cells_are_invalid(self):
        board = EnglishBoard(7)
        assert board.get_cell(0, 0) == INVALID
        assert board.get_cell(0, 6) == INVALID
        assert board.get_cell(6, 0) == INVALID
        assert board.get_cell(6, 6) == INVALID

    def test_peg_count_at_start(self):
        board = EnglishBoard(7)
        # 7x7 minus 4 corners of 2x2 minus 1 empty center
        # English board has 33 valid cells, 32 pegs at start
        assert board.count_pegs() == 32


# ── Move Validation ────────────────────────────────────────────────────────

class TestMoveValidation:

    def setup_method(self):
        self.board = EnglishBoard(7)
        # Center (3,3) is empty. (3,1) has a peg, (3,2) has a peg.
        # So (3,1) → (3,3) is a valid jump over (3,2).

    def test_valid_move_right(self):
        assert self.board.is_valid_move(3, 1, 3, 3) is True

    def test_valid_move_left(self):
        # (3,5) → (3,3) over (3,4)
        assert self.board.is_valid_move(3, 5, 3, 3) is True

    def test_valid_move_down(self):
        # (1,3) → (3,3) over (2,3)
        assert self.board.is_valid_move(1, 3, 3, 3) is True

    def test_valid_move_up(self):
        # (5,3) → (3,3) over (4,3)
        assert self.board.is_valid_move(5, 3, 3, 3) is True

    def test_invalid_move_no_peg_at_source(self):
        # (3,3) is empty — can't move from there
        assert self.board.is_valid_move(3, 3, 3, 1) is False

    def test_invalid_move_destination_not_empty(self):
        # (3,0) has a peg, (3,2) has a peg — destination is occupied
        assert self.board.is_valid_move(3, 0, 3, 2) is False

    def test_invalid_move_no_middle_peg(self):
        # Manually clear the middle peg
        self.board.set_cell(3, 2, EMPTY)
        # Now (3,1) → (3,3) has no peg to jump over
        assert self.board.is_valid_move(3, 1, 3, 3) is False

    def test_invalid_diagonal_move(self):
        assert self.board.is_valid_move(3, 1, 1, 3) is False

    def test_invalid_one_step_move(self):
        assert self.board.is_valid_move(3, 1, 3, 2) is False


# ── Move Execution ─────────────────────────────────────────────────────────

class TestMoveExecution:

    def setup_method(self):
        self.board = EnglishBoard(7)

    def test_make_valid_move_returns_true(self):
        result = self.board.make_move(3, 1, 3, 3)
        assert result is True

    def test_make_valid_move_updates_source(self):
        self.board.make_move(3, 1, 3, 3)
        assert self.board.get_cell(3, 1) == EMPTY

    def test_make_valid_move_removes_jumped_peg(self):
        self.board.make_move(3, 1, 3, 3)
        assert self.board.get_cell(3, 2) == EMPTY

    def test_make_valid_move_places_peg_at_destination(self):
        self.board.make_move(3, 1, 3, 3)
        assert self.board.get_cell(3, 3) == PEG

    def test_make_valid_move_reduces_peg_count(self):
        before = self.board.count_pegs()
        self.board.make_move(3, 1, 3, 3)
        assert self.board.count_pegs() == before - 1

    def test_make_invalid_move_returns_false(self):
        result = self.board.make_move(3, 3, 3, 1)  # source is empty
        assert result is False

    def test_make_invalid_move_does_not_change_board(self):
        before = self.board.count_pegs()
        self.board.make_move(3, 3, 3, 1)
        assert self.board.count_pegs() == before


# ── Game Over Detection ────────────────────────────────────────────────────

class TestGameOver:

    def test_fresh_board_not_game_over(self):
        board = EnglishBoard(7)
        assert board.is_game_over() is False

    def test_game_over_when_no_moves(self):
        """Manually construct a board where no moves are possible."""
        board = EnglishBoard(7)
        # Clear everything
        for r in range(board.size):
            for c in range(len(board.grid[r])):
                if board.grid[r][c] != INVALID:
                    board.grid[r][c] = EMPTY
        # Place one isolated peg — no neighbors to jump over
        board.set_cell(3, 3, PEG)
        assert board.is_game_over() is True

    def test_has_valid_moves_on_fresh_board(self):
        board = EnglishBoard(7)
        assert board.has_valid_moves() is True


# ── Rating System ──────────────────────────────────────────────────────────

class TestRating:

    def _board_with_n_pegs(self, n):
        board = EnglishBoard(7)
        for r in range(board.size):
            for c in range(len(board.grid[r])):
                if board.grid[r][c] != INVALID:
                    board.grid[r][c] = EMPTY
        placed = 0
        for r in range(board.size):
            for c in range(len(board.grid[r])):
                if board.grid[r][c] == EMPTY and placed < n:
                    board.grid[r][c] = PEG
                    placed += 1
        return board

    def test_rating_outstanding(self):
        board = self._board_with_n_pegs(1)
        assert board.get_rating() == "Outstanding"

    def test_rating_very_good(self):
        board = self._board_with_n_pegs(2)
        assert board.get_rating() == "Very Good"

    def test_rating_good(self):
        board = self._board_with_n_pegs(3)
        assert board.get_rating() == "Good"

    def test_rating_average(self):
        board = self._board_with_n_pegs(10)
        assert board.get_rating() == "Average"


# ── Board Factory ──────────────────────────────────────────────────────────

class TestBoardFactory:

    def test_create_english_board(self):
        board = create_board("english", 7)
        assert isinstance(board, EnglishBoard)

    def test_create_hexagon_board(self):
        board = create_board("hexagon", 7)
        assert isinstance(board, HexagonBoard)

    def test_create_diamond_board(self):
        board = create_board("diamond", 7)
        assert isinstance(board, DiamondBoard)

    def test_create_board_case_insensitive(self):
        board = create_board("English", 7)
        assert isinstance(board, EnglishBoard)

    def test_create_board_invalid_type(self):
        with pytest.raises(ValueError):
            create_board("triangle", 7)

    def test_board_size_passed_correctly(self):
        board = create_board("english", 9)
        assert board.size == 9
