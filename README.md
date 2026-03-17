# CS449-Peg-Solitaire

Peg Solitaire Game for CS449 Software Engineering — Spring 2026  
University of Missouri-Kansas City  
Student: Colton Hanson

## Description
A fully playable Peg Solitaire game with a graphical user interface (GUI) built in Python using Tkinter. Supports three board types: English, Hexagon, and Diamond.

## Project Structure
- `board.py` — Core game logic (move validation, game over detection, ratings)
- `board_types.py` — Board shape definitions (EnglishBoard, HexagonBoard, DiamondBoard)
- `gui.py` — Tkinter GUI (all user interface code)
- `test_board.py` — 35 pytest unit tests

## How to Run
```bash
python gui.py
```

## How to Run Tests
```bash
python -m pytest test_board.py -v
```

## Features
- Choose board size (5–11, odd) and type
- Preview board shape before starting
- Start a new game
- Make moves by clicking pegs
- Automatic game over detection with player rating
