# CS449-Peg-Solitaire

Peg Solitaire Game for CS449 Software Engineering — Spring 2026  
University of Missouri-Kansas City  
Student: Colton Hanson

## Description
A fully playable Peg Solitaire game with a graphical user interface (GUI) built in Python using Tkinter. Supports three board types and two game modes.

## Project Structure
- `board.py` — Core game logic (move validation, game over detection, ratings)
- `board_types.py` — Board shape definitions (EnglishBoard, HexagonBoard, DiamondBoard)
- `game.py` — Game session classes (Game base, ManualGame, AutomatedGame)
- `gui.py` — Tkinter GUI (all user interface code)
- `test_board.py` — 53 pytest unit tests

## How to Run
```bash
py -3.10 gui.py
```

## How to Run Tests
```bash
python -m pytest test_board.py -v
```

## Features
- Choose board size (5–11, odd) and type (English, Hexagon, Diamond)
- Choose game mode: Manual or Autoplay
- Preview board shape before starting
- Start a new game
- Make moves by clicking pegs (Manual mode)
- Autoplay — computer plays random valid moves every 300ms
- Randomize board state mid-game
- Automatic game over detection with player rating
