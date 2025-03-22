# Chessboard Editor with Attack Visualization

This Python project creates an interactive chessboard editor using **python‑chess** and **pygame**. It features:

- **Free Piece Movement:** Drag and drop pieces anywhere on the board.
- **Toolbox Panel:** A right-hand panel displays a set of chess pieces.
  - Drag a piece from the panel onto the board to add it.
  - Drag a piece from the board and drop it onto the panel to remove it.
- **Attack Visualization:** Each board square shows the number of white attackers (top left) and black attackers (bottom right) based on the current board state.
- **Reset Buttons:** Two buttons are provided:
  - **Clear:** Reset the board to an empty state.
  - **Start:** Reset the board to the standard starting position.

## Requirements

- Python 3.x
- [pygame](https://www.pygame.org/)
- [python‑chess](https://pypi.org/project/python-chess/)

## Installation

Install the required packages using pip:

```bash
pip install pygame python-chess
```

## Running the Project

Run the script from the command line:

```bash
python your_script_name.py
```

Replace `your_script_name.py` with the name of your Python file.

## Usage

- **Adding a Piece:**  
  Drag a piece from the right-hand panel (toolbox) and drop it onto the chessboard.

- **Moving a Piece:**  
  Click and drag a piece from the board to move it to another square.

- **Removing a Piece:**  
  Drag a piece from the board and drop it onto the right-hand panel.

- **Resetting the Board:**  
  Click the **Clear** button to empty the board or the **Start** button to reset to the standard chess starting position.

Enjoy customizing your chessboard and exploring attack visualizations!
