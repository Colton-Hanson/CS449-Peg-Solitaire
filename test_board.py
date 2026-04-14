"""
test_board.py - pytest unit tests for Peg Solitaire game logic.
Tests cover board initialization, move validation, move execution, game-over detection,
and the ManualGame / AutomatedGame session classes.
UI code (gui.py) is NOT imported here — pure logic tests only.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from board import Board, PEG, EMPTY, INVALID
from board_types import EnglishBoard, HexagonBoard, DiamondBoard, create_board
from game import Game, ManualGame, AutomatedGame


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


# ── ManualGame ─────────────────────────────────────────────────────────────

class TestManualGame:

    def setup_method(self):
        self.game = ManualGame(EnglishBoard(7))

    def test_manual_game_is_subclass_of_game(self):
        assert isinstance(self.game, Game)

    def test_select_peg_returns_valid_destinations(self):
        # (3,1) can jump to (3,3) over (3,2) on a fresh English board
        dests = self.game.select_peg(3, 1)
        assert (3, 3) in dests

    def test_select_peg_sets_selected_attribute(self):
        self.game.select_peg(3, 1)
        assert self.game.selected == (3, 1)

    def test_select_peg_with_no_moves_returns_empty(self):
        # Empty cell — no peg to select
        dests = self.game.select_peg(3, 3)
        assert dests == []
        assert self.game.selected is None

    def test_deselect_clears_selection(self):
        self.game.select_peg(3, 1)
        self.game.deselect()
        assert self.game.selected is None
        assert self.game.valid_destinations == []

    def test_attempt_move_succeeds_and_updates_board(self):
        self.game.select_peg(3, 1)
        result = self.game.attempt_move(3, 3)
        assert result is True
        assert self.game.board.get_cell(3, 3) == PEG
        assert self.game.board.get_cell(3, 1) == EMPTY

    def test_attempt_move_clears_selection_on_success(self):
        self.game.select_peg(3, 1)
        self.game.attempt_move(3, 3)
        assert self.game.selected is None
        assert self.game.valid_destinations == []

    def test_attempt_move_without_selection_returns_false(self):
        result = self.game.attempt_move(3, 3)
        assert result is False

    def test_move_count_increments_on_success(self):
        self.game.select_peg(3, 1)
        self.game.attempt_move(3, 3)
        assert self.game.move_count == 1

    def test_move_count_does_not_increment_on_failure(self):
        self.game.attempt_move(3, 3)  # no peg selected
        assert self.game.move_count == 0


# ── AutomatedGame ──────────────────────────────────────────────────────────

class TestAutomatedGame:

    def setup_method(self):
        self.game = AutomatedGame(EnglishBoard(7))

    def test_automated_game_is_subclass_of_game(self):
        assert isinstance(self.game, Game)

    def test_play_random_move_returns_a_move_tuple(self):
        move = self.game.play_random_move()
        assert move is not None
        assert len(move) == 4  # (from_row, from_col, to_row, to_col)

    def test_play_random_move_reduces_peg_count(self):
        before = self.game.get_pegs()
        self.game.play_random_move()
        assert self.game.get_pegs() == before - 1

    def test_play_random_move_increments_move_count(self):
        self.game.play_random_move()
        assert self.game.move_count == 1

    def test_play_random_move_returns_none_when_game_over(self):
        # Clear the board to a stuck state: one isolated peg
        for r in range(self.game.board.size):
            for c in range(len(self.game.board.grid[r])):
                if self.game.board.grid[r][c] != INVALID:
                    self.game.board.grid[r][c] = EMPTY
        self.game.board.set_cell(3, 3, PEG)
        result = self.game.play_random_move()
        assert result is None

    def test_play_to_end_reaches_game_over(self):
        self.game.play_to_end()
        assert self.game.is_game_over() is True

    def test_play_to_end_returns_positive_move_count(self):
        count = self.game.play_to_end()
        assert count > 0

    def test_multiple_random_moves_are_all_valid(self):
        """Each move should decrease peg count by exactly 1."""
        for _ in range(5):
            before = self.game.get_pegs()
            move = self.game.play_random_move()
            if move is None:
                break
            assert self.game.get_pegs() == before - 1


# ── Recorder Tests ─────────────────────────────────────────────────────────

import tempfile
import os
from recorder import GameRecorder, GameReplayer


class TestGameRecorder:

    def test_recorder_saves_file(self):
        rec = GameRecorder("English", 7, "Manual")
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            rec.save(path)
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_recorder_writes_header(self):
        rec = GameRecorder("English", 7, "Manual")
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            path = f.name
        try:
            rec.save(path)
            content = open(path).read()
            assert "BOARD_TYPE=English" in content
            assert "BOARD_SIZE=7" in content
            assert "MODE=Manual" in content
        finally:
            os.unlink(path)

    def test_recorder_writes_moves(self):
        rec = GameRecorder("English", 7, "Manual")
        rec.record_move(3, 1, 3, 3)
        rec.record_move(5, 2, 3, 2)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            rec.save(path)
            content = open(path).read()
            assert "MOVE 3 1 3 3" in content
            assert "MOVE 5 2 3 2" in content
        finally:
            os.unlink(path)

    def test_recorder_writes_randomize(self):
        board = EnglishBoard()
        rec = GameRecorder("English", 7, "Manual")
        rec.record_randomize(board.grid)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            rec.save(path)
            content = open(path).read()
            assert "RANDOMIZE" in content
        finally:
            os.unlink(path)


class TestGameReplayer:

    def _make_recording(self, moves=None, board_type="English", size=7, mode="Manual"):
        rec = GameRecorder(board_type, size, mode)
        for move in (moves or []):
            rec.record_move(*move)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            path = f.name
        rec.save(path)
        return path

    def test_replayer_reads_header(self):
        path = self._make_recording()
        try:
            r = GameReplayer(path)
            assert r.board_type == "English"
            assert r.board_size == 7
            assert r.mode == "Manual"
        finally:
            os.unlink(path)

    def test_replayer_reads_moves(self):
        path = self._make_recording(moves=[(3, 1, 3, 3), (5, 2, 3, 2)])
        try:
            r = GameReplayer(path)
            assert len(r.events) == 2
            assert r.events[0] == ("MOVE", 3, 1, 3, 3)
            assert r.events[1] == ("MOVE", 5, 2, 3, 2)
        finally:
            os.unlink(path)

    def test_replayer_has_next(self):
        path = self._make_recording(moves=[(3, 1, 3, 3)])
        try:
            r = GameReplayer(path)
            assert r.has_next() is True
            r.next_event()
            assert r.has_next() is False
        finally:
            os.unlink(path)

    def test_replayer_next_event_returns_correct_type(self):
        path = self._make_recording(moves=[(3, 1, 3, 3)])
        try:
            r = GameReplayer(path)
            event = r.next_event()
            assert event[0] == "MOVE"
        finally:
            os.unlink(path)

    def test_replayer_reset(self):
        path = self._make_recording(moves=[(3, 1, 3, 3)])
        try:
            r = GameReplayer(path)
            r.next_event()
            assert r.has_next() is False
            r.reset()
            assert r.has_next() is True
        finally:
            os.unlink(path)

    def test_replayer_no_events_when_empty(self):
        path = self._make_recording(moves=[])
        try:
            r = GameReplayer(path)
            assert r.has_next() is False
        finally:
            os.unlink(path)