import pygame
import chess

# ─────────────────────────────────────────────────────────────────────────────
# Window layout constants
BOARD_PANEL_WIDTH = 640     # Chessboard area: 640x640 pixels
RIGHT_PANEL_WIDTH = 200     # Toolbox area on the right
TOTAL_WIDTH = BOARD_PANEL_WIDTH + RIGHT_PANEL_WIDTH
TOTAL_HEIGHT = 640

# Chessboard square size (each square is square)
SQUARE_SIZE = BOARD_PANEL_WIDTH // 8

# Colors for board squares
LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)

# Colors for right panel and buttons
PANEL_BG_COLOR = (200, 200, 200)
BUTTON_COLOR = (150, 150, 150)
BUTTON_HOVER_COLOR = (170, 170, 170)
BUTTON_TEXT_COLOR = (0, 0, 0)

# Margin for text drawing
MARGIN = 5

# ─────────────────────────────────────────────────────────────────────────────
# Define piece order (for both white and black) for the toolbox grid
PIECE_ORDER = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]

# ─────────────────────────────────────────────────────────────────────────────
def piece_unicode(piece):
    """Return the Unicode symbol for a chess piece."""
    if piece.color == chess.WHITE:
        symbols = {
            chess.PAWN:   "♙",
            chess.KNIGHT: "♘",
            chess.BISHOP: "♗",
            chess.ROOK:   "♖",
            chess.QUEEN:  "♕",
            chess.KING:   "♔"
        }
    else:
        symbols = {
            chess.PAWN:   "♟",
            chess.KNIGHT: "♞",
            chess.BISHOP: "♝",
            chess.ROOK:   "♜",
            chess.QUEEN:  "♛",
            chess.KING:   "♚"
        }
    return symbols.get(piece.piece_type, "?")

def draw_text_with_outline(surface, text, font, pos, text_color, outline_color):
    """
    Draw text with an outline for better readability.
    Blits the outline (offset in four directions) then the main text.
    """
    base_text = font.render(text, True, text_color)
    outline_text = font.render(text, True, outline_color)
    for dx in (-1, 1):
        for dy in (-1, 1):
            surface.blit(outline_text, (pos[0] + dx, pos[1] + dy))
    surface.blit(base_text, pos)

# ─────────────────────────────────────────────────────────────────────────────
def create_toolbox_layout(panel_x, panel_y, panel_width, panel_height):
    """
    Create and return the rectangles for the two buttons and the piece icons.
    Returns:
        buttons: dict with keys "clear" and "start" mapping to their rects.
        piece_icons: list of dicts, each with keys: "rect" and "piece".
                     The list will contain one icon for each piece in the toolbox.
    """
    buttons = {}
    # Define button dimensions
    btn_width = panel_width - 20
    btn_height = 40
    btn_margin = 10
    # Clear button at top
    clear_rect = pygame.Rect(panel_x + 10, panel_y + 10, btn_width, btn_height)
    # Start button below it
    start_rect = pygame.Rect(panel_x + 10, panel_y + 10 + btn_height + 5, btn_width, btn_height)
    buttons["clear"] = clear_rect
    buttons["start"] = start_rect

    # Define piece grid area below the buttons:
    grid_top = panel_y + 10 + 2 * (btn_height + 5)  # starting y for piece icons
    grid_cell_width = panel_width // 2  # two columns: white and black
    grid_cell_height = (panel_height - grid_top - 10) // len(PIECE_ORDER)  # one row per piece type

    piece_icons = []
    # For each piece type in order, add two icons (one white, one black)
    for row, piece_type in enumerate(PIECE_ORDER):
        # White piece icon
        white_rect = pygame.Rect(
            panel_x,
            grid_top + row * grid_cell_height,
            grid_cell_width,
            grid_cell_height
        )
        piece_icons.append({"rect": white_rect, "piece": chess.Piece(piece_type, chess.WHITE)})
        # Black piece icon
        black_rect = pygame.Rect(
            panel_x + grid_cell_width,
            grid_top + row * grid_cell_height,
            grid_cell_width,
            grid_cell_height
        )
        piece_icons.append({"rect": black_rect, "piece": chess.Piece(piece_type, chess.BLACK)})

    return buttons, piece_icons

# ─────────────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
    pygame.display.set_caption("Chessboard Editor with Attack Visualization")
    clock = pygame.time.Clock()

    # Use a font that supports chess glyphs (arialunicode works for you)
    font_name = pygame.font.match_font("arialunicode")
    board_piece_font = pygame.font.Font(font_name, 50)
    # For attacker counts
    number_font = pygame.font.SysFont("Arial", SQUARE_SIZE // 3, bold=True)
    # For the toolbox piece icons (smaller)
    toolbox_piece_font = pygame.font.Font(font_name, 50)

    # ────────────────
    # Initialize the chess board using python-chess.
    board = chess.Board()  # starting position

    # Drag and drop state variables.
    dragging = False           # True if a piece is being dragged
    dragging_piece = None      # Either a chess.Piece (from board) or a tuple (color, piece_type) from panel
    dragging_source = None     # "board" or "panel"
    dragging_offset = (0, 0)   # Offset within the source rectangle where the drag started
    dragging_pos = None        # Current mouse position while dragging
    dragging_origin_square = None  # If dragging from board, store the original square (for removal)

    # Right panel layout (toolbox)
    panel_x = BOARD_PANEL_WIDTH
    panel_y = 0
    panel_width = RIGHT_PANEL_WIDTH
    panel_height = TOTAL_HEIGHT
    buttons, piece_icons = create_toolbox_layout(panel_x, panel_y, panel_width, panel_height)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ── Mouse Button Down ───────────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos

                # Check if the click is in the right panel (toolbox) or board.
                if mouse_x >= BOARD_PANEL_WIDTH:
                    # Right panel: check if clicking a button first.
                    clicked_button = None
                    for key, rect in buttons.items():
                        if rect.collidepoint(mouse_x, mouse_y):
                            clicked_button = key
                            break
                    if clicked_button == "clear":
                        board.clear()  # remove all pieces
                    elif clicked_button == "start":
                        board.set_fen(chess.STARTING_FEN)
                    else:
                        # Otherwise, check if clicking on a piece icon.
                        for icon in piece_icons:
                            if icon["rect"].collidepoint(mouse_x, mouse_y):
                                dragging = True
                                dragging_source = "panel"
                                # For a panel piece, we store a tuple: (color, piece_type)
                                piece_info = icon["piece"]
                                dragging_piece = (piece_info.color, piece_info.piece_type)
                                # Calculate offset relative to the icon's rect top-left.
                                dragging_offset = (mouse_x - icon["rect"].x, mouse_y - icon["rect"].y)
                                dragging_pos = event.pos
                                break
                else:
                    # Left panel (board area): check if a piece is on the clicked square.
                    file = mouse_x // SQUARE_SIZE
                    rank = 7 - (mouse_y // SQUARE_SIZE)
                    square = chess.square(file, rank)
                    piece = board.piece_at(square)
                    if piece:
                        dragging = True
                        dragging_source = "board"
                        dragging_piece = piece
                        dragging_origin_square = square
                        # Remove the piece from the board temporarily while dragging.
                        board.remove_piece_at(square)
                        square_x = file * SQUARE_SIZE
                        square_y = (7 - rank) * SQUARE_SIZE
                        dragging_offset = (mouse_x - square_x, mouse_y - square_y)
                        dragging_pos = event.pos

            # ── Mouse Motion ─────────────────────────────────────────────────────
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    dragging_pos = event.pos

            # ── Mouse Button Up ───────────────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging:
                    mouse_x, mouse_y = event.pos
                    # Determine drop location:
                    if mouse_x < BOARD_PANEL_WIDTH:
                        # Dropped on the board
                        file = mouse_x // SQUARE_SIZE
                        rank = 7 - (mouse_y // SQUARE_SIZE)
                        dest_square = chess.square(file, rank)
                        # If dragging from the board, move the piece; if from the panel, add a new piece.
                        if dragging_source == "board":
                            board.set_piece_at(dest_square, dragging_piece)
                        elif dragging_source == "panel":
                            color, piece_type = dragging_piece
                            board.set_piece_at(dest_square, chess.Piece(piece_type, color))
                    else:
                        # Dropped on the right panel:
                        # If dragging from the board, remove the piece (i.e. do nothing since it's already removed).
                        # If dragging from the panel, just cancel the drag.
                        pass
                    # Reset dragging state
                    dragging = False
                    dragging_piece = None
                    dragging_source = None
                    dragging_origin_square = None
                    dragging_pos = None

        # ──────────────────────────────
        # Draw the board (left panel)
        for rank in range(8):
            for file in range(8):
                x = file * SQUARE_SIZE
                y = (7 - rank) * SQUARE_SIZE
                square_rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
                square_color = LIGHT_COLOR if (rank + file) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(screen, square_color, square_rect)

                # Determine square index and attacker counts using python‑chess.
                square_index = chess.square(file, rank)
                white_attackers = board.attackers(chess.WHITE, square_index)
                black_attackers = board.attackers(chess.BLACK, square_index)
                white_count = len(white_attackers)
                black_count = len(black_attackers)

                # Draw white attackers count (top left) if nonzero.
                if white_count > 0:
                    count_text = str(white_count)
                    pos = (x + MARGIN, y + MARGIN)
                    draw_text_with_outline(screen, count_text, number_font, pos,
                                           (255, 255, 255), (0, 0, 0))
                # Draw black attackers count (top right) if nonzero.
                if black_count > 0:
                    count_text = str(black_count)
                    text_surface = number_font.render(count_text, True, (0, 0, 0))
                    text_rect = text_surface.get_rect()
                    pos = (x + SQUARE_SIZE - text_rect.width - MARGIN,
                           y + MARGIN)
                    draw_text_with_outline(screen, count_text, number_font, pos,
                                           (0, 0, 0), (255, 255, 255))

        # Draw pieces from board state.
        for square in chess.SQUARES:
            # Skip the square from which a piece is currently being dragged.
            if dragging_source == "board" and square == dragging_origin_square:
                continue
            piece = board.piece_at(square)
            if piece:
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                x = file * SQUARE_SIZE
                y = (7 - rank) * SQUARE_SIZE
                symbol = piece_unicode(piece)
                # Determine color and outline
                if piece.color == chess.WHITE:
                    piece_color = (255, 255, 255)
                    outline_color = (0, 0, 0)
                else:
                    piece_color = (0, 0, 0)
                    outline_color = (255, 255, 255)
                text_surface = board_piece_font.render(symbol, True, piece_color)
                text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2,
                                                           y + SQUARE_SIZE // 2))
                # Draw outline for clarity.
                for dx in (-2, 2):
                    for dy in (-2, 2):
                        outline_surface = board_piece_font.render(symbol, True, outline_color)
                        outline_rect = outline_surface.get_rect(center=(x + SQUARE_SIZE // 2 + dx,
                                                                         y + SQUARE_SIZE // 2 + dy))
                        screen.blit(outline_surface, outline_rect)
                screen.blit(text_surface, text_rect)

        # If dragging a piece, draw it following the mouse.
        if dragging and dragging_pos:
            draw_x = dragging_pos[0] - dragging_offset[0]
            draw_y = dragging_pos[1] - dragging_offset[1]
            # For panel-sourced pieces, construct a chess.Piece-like symbol
            if dragging_source == "panel":
                color, piece_type = dragging_piece
                temp_piece = chess.Piece(piece_type, color)
                symbol = piece_unicode(temp_piece)
            else:
                symbol = piece_unicode(dragging_piece)
            if (dragging_source == "board" and dragging_piece.color == chess.WHITE) or \
               (dragging_source == "panel" and dragging_piece[0] == chess.WHITE):
                piece_color = (255, 255, 255)
                outline_color = (0, 0, 0)
            else:
                piece_color = (0, 0, 0)
                outline_color = (255, 255, 255)
            # Use board piece font to draw the dragging piece.
            text_surface = board_piece_font.render(symbol, True, piece_color)
            text_rect = text_surface.get_rect(center=(draw_x + SQUARE_SIZE // 2,
                                                       draw_y + SQUARE_SIZE // 2))
            for dx in (-2, 2):
                for dy in (-2, 2):
                    outline_surface = board_piece_font.render(symbol, True, outline_color)
                    outline_rect = outline_surface.get_rect(center=(draw_x + SQUARE_SIZE // 2 + dx,
                                                                     draw_y + SQUARE_SIZE // 2 + dy))
                    screen.blit(outline_surface, outline_rect)
            screen.blit(text_surface, text_rect)

        # ──────────────────────────────
        # Draw the right panel background
        panel_rect = pygame.Rect(BOARD_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, TOTAL_HEIGHT)
        pygame.draw.rect(screen, PANEL_BG_COLOR, panel_rect)

        # Draw buttons in the toolbox.
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for key, rect in buttons.items():
            # Change color on hover
            if rect.collidepoint(mouse_x, mouse_y):
                color = BUTTON_HOVER_COLOR
            else:
                color = BUTTON_COLOR
            pygame.draw.rect(screen, color, rect)
            # Draw button text centered in the rect.
            if key == "clear":
                text = "Clear"
            elif key == "start":
                text = "Start"
            btn_font = pygame.font.SysFont("Arial", 24, bold=True)
            text_surf = btn_font.render(text, True, BUTTON_TEXT_COLOR)
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        # Draw piece icons on the right panel.
        for icon in piece_icons:
            rect = icon["rect"]
            # Draw a border for the icon cell.
            pygame.draw.rect(screen, (100, 100, 100), rect, 1)
            piece = icon["piece"]
            symbol = piece_unicode(piece)
            text_surf = toolbox_piece_font.render(symbol, True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()