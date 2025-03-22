import pygame
import chess
import chess.pgn
import io

# ─────────────────────────────────────────────────────────────────────────────
# Constants & Layout
BOARD_PANEL_WIDTH = 640     # Chessboard area (left)
RIGHT_PANEL_WIDTH = 200     # Right panel for controls
TOTAL_WIDTH = BOARD_PANEL_WIDTH + RIGHT_PANEL_WIDTH
TOTAL_HEIGHT = 640
SQUARE_SIZE = BOARD_PANEL_WIDTH // 8

# Colors
LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)
PANEL_BG_COLOR = (200, 200, 200)
BUTTON_COLOR = (150, 150, 150)
BUTTON_HOVER_COLOR = (170, 170, 170)
BUTTON_TEXT_COLOR = (0, 0, 0)
TEXT_INPUT_BG = (255, 255, 255)
TEXT_INPUT_BORDER = (0, 0, 0)
MARGIN = 5

# ─────────────────────────────────────────────────────────────────────────────
# A simple InputBox class (supports single- or multi-line input)
class InputBox:
    def __init__(self, x, y, w, h, text='', multiline=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = TEXT_INPUT_BG
        self.text = text
        self.txt_surface = pygame.font.SysFont("Arial", 16).render(text, True, (0, 0, 0))
        self.active = False
        self.multiline = multiline
        self.font = pygame.font.SysFont("Arial", 16)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active if click inside the input box.
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                if not self.multiline:
                    self.active = False
                else:
                    self.text += "\n"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, (0, 0, 0))

    def draw(self, screen):
        # Draw the input box
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, TEXT_INPUT_BORDER, self.rect, 2)
        # For multi-line, split text into lines:
        if self.multiline:
            lines = self.text.splitlines()
            y_offset = 0
            for line in lines:
                txt_surf = self.font.render(line, True, (0, 0, 0))
                screen.blit(txt_surf, (self.rect.x+5, self.rect.y+5+y_offset))
                y_offset += txt_surf.get_height() + 2
        else:
            screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))

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
    """Draw text with an outline for better readability."""
    base_text = font.render(text, True, text_color)
    outline_text = font.render(text, True, outline_color)
    for dx in (-1, 1):
        for dy in (-1, 1):
            surface.blit(outline_text, (pos[0] + dx, pos[1] + dy))
    surface.blit(base_text, pos)

# ─────────────────────────────────────────────────────────────────────────────
# Define toolbox piece icons (same as before)
PIECE_ORDER = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
def create_toolbox_layout(panel_x, panel_y, panel_width, panel_height):
    # We'll start the piece icons lower, after our PGN/FEN UI.
    icons = []
    grid_top = panel_y 
    grid_cell_width = panel_width // 2
    grid_cell_height = (panel_height - grid_top - 10) // len(PIECE_ORDER)
    for row, piece_type in enumerate(PIECE_ORDER):
        white_rect = pygame.Rect(
            panel_x,
            grid_top + row * grid_cell_height,
            grid_cell_width,
            grid_cell_height
        )
        icons.append({"rect": white_rect, "piece": chess.Piece(piece_type, chess.WHITE)})
        black_rect = pygame.Rect(
            panel_x + grid_cell_width,
            grid_top + row * grid_cell_height,
            grid_cell_width,
            grid_cell_height
        )
        icons.append({"rect": black_rect, "piece": chess.Piece(piece_type, chess.BLACK)})
    return icons

# ─────────────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
    pygame.display.set_caption("Chess Editor with PGN/FEN & Attack Visualization")
    clock = pygame.time.Clock()

    # Fonts
    font_name = pygame.font.match_font("arialunicode")
    board_piece_font = pygame.font.Font(font_name, 50)  # pieces on board are size 50 now
    number_font = pygame.font.SysFont("Arial", SQUARE_SIZE // 3, bold=True)  # for attacker counts
    toolbox_piece_font = pygame.font.Font(font_name, 50)

    # Chess board
    board = chess.Board()

    # PGN state
    locked = False
    pgn_moves = []    # list of moves loaded from PGN
    move_index = 0
    pgn_game = None

    # Drag & drop state
    dragging = False
    dragging_piece = None
    dragging_source = None  # "board" or "panel"
    dragging_offset = (0, 0)
    dragging_pos = None
    dragging_origin_square = None

    # Create InputBoxes for FEN and PGN in the right panel.
    # FEN Input (single line)
    fen_input = InputBox(BOARD_PANEL_WIDTH + 10, 10, 180, 30, text="FEN here")
    # PGN Input (multi-line)
    pgn_input = InputBox(BOARD_PANEL_WIDTH + 10, 50, 180, 70, text="PGN here", multiline=True)

    # Define buttons (as dictionary mapping key->pygame.Rect)
    buttons = {
        "load_fen": pygame.Rect(BOARD_PANEL_WIDTH + 10, 130, 80, 30),
        "export_fen": pygame.Rect(BOARD_PANEL_WIDTH + 100, 130, 90, 30),
        "load_pgn": pygame.Rect(BOARD_PANEL_WIDTH + 10, 170, 80, 30),
        "export_pgn": pygame.Rect(BOARD_PANEL_WIDTH + 100, 170, 90, 30),
        "prev": pygame.Rect(BOARD_PANEL_WIDTH + 10, 210, 80, 30),
        "next": pygame.Rect(BOARD_PANEL_WIDTH + 100, 210, 90, 30),
        "lock_toggle": pygame.Rect(BOARD_PANEL_WIDTH + 10, 250, 180, 30),
        "clear": pygame.Rect(BOARD_PANEL_WIDTH + 10, 290, 80, 30),
        "start": pygame.Rect(BOARD_PANEL_WIDTH + 100, 290, 90, 30)
    }

    # Toolbox piece icons (for adding pieces via drag from panel)
    toolbox_icons = create_toolbox_layout(BOARD_PANEL_WIDTH, 330, RIGHT_PANEL_WIDTH, TOTAL_HEIGHT)

    running = True
    while running:
        for event in pygame.event.get():
            # Handle quitting
            if event.type == pygame.QUIT:
                running = False

            # Handle input boxes (FEN and PGN)
            fen_input.handle_event(event)
            pgn_input.handle_event(event)

            # Mouse events for buttons & dragging
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos

                # If click is on right panel, check for buttons
                if mouse_x >= BOARD_PANEL_WIDTH:
                    # Check each button:
                    for key, rect in buttons.items():
                        if rect.collidepoint(mouse_x, mouse_y):
                            if key == "load_fen":
                                try:
                                    board.set_fen(fen_input.text.strip())
                                    locked = False
                                    pgn_moves = []
                                    move_index = 0
                                except Exception as e:
                                    print("Invalid FEN:", e)
                            elif key == "export_fen":
                                fen_input.text = board.fen()
                                fen_input.txt_surface = fen_input.font.render(fen_input.text, True, (0, 0, 0))
                            elif key == "load_pgn":
                                try:
                                    pgn_text = pgn_input.text.strip()
                                    pgn_io = io.StringIO(pgn_text)
                                    game = chess.pgn.read_game(pgn_io)
                                    if game is None:
                                        raise Exception("Could not parse PGN")
                                    # Extract moves from the game:
                                    board.reset()
                                    pgn_moves = list(game.mainline_moves())
                                    move_index = 0
                                    locked = True
                                    pgn_game = game
                                except Exception as e:
                                    print("Invalid PGN:", e)
                            elif key == "export_pgn":
                                if locked and pgn_game:
                                    # Export PGN up to current move
                                    export_game = chess.pgn.Game()
                                    export_game.headers = pgn_game.headers
                                    node = export_game
                                    temp_board = chess.Board()
                                    for move in pgn_moves[:move_index]:
                                        node = node.add_main_variation(move)
                                        temp_board.push(move)
                                    exporter = io.StringIO()
                                    print(export_game, file=exporter, end="\n")
                                    pgn_input.text = exporter.getvalue()
                                    pgn_input.txt_surface = pgn_input.font.render(pgn_input.text, True, (0, 0, 0))
                                else:
                                    # Not locked – export current position as a one-move PGN.
                                    pgn_input.text = "[FEN \"" + board.fen() + "\"]\n\n"
                                    pgn_input.txt_surface = pgn_input.font.render(pgn_input.text, True, (0, 0, 0))
                            elif key == "prev":
                                if locked and move_index > 0:
                                    board.pop()
                                    move_index -= 1
                            elif key == "next":
                                if locked and move_index < len(pgn_moves):
                                    board.push(pgn_moves[move_index])
                                    move_index += 1
                            elif key == "lock_toggle":
                                locked = not locked
                            elif key == "clear":
                                board.clear()
                                locked = False
                                pgn_moves = []
                                move_index = 0
                            elif key == "start":
                                board.reset()
                                locked = False
                                pgn_moves = []
                                move_index = 0
                            break  # only one button activated per click

                    # If not clicking on a button, check toolbox icons for drag (adding pieces)
                    else:
                        for icon in toolbox_icons:
                            if icon["rect"].collidepoint(mouse_x, mouse_y):
                                dragging = True
                                dragging_source = "panel"
                                piece_info = icon["piece"]
                                dragging_piece = (piece_info.color, piece_info.piece_type)
                                dragging_offset = (mouse_x - icon["rect"].x, mouse_y - icon["rect"].y)
                                dragging_pos = event.pos
                                break

                else:
                    # Click on the board
                    file = mouse_x // SQUARE_SIZE
                    rank = 7 - (mouse_y // SQUARE_SIZE)
                    square = chess.square(file, rank)
                    piece = board.piece_at(square)
                    if piece:
                        # Auto-unlock if board is locked
                        if locked:
                            locked = False
                        dragging = True
                        dragging_source = "board"
                        dragging_piece = piece
                        dragging_origin_square = square
                        board.remove_piece_at(square)
                        square_x = file * SQUARE_SIZE
                        square_y = (7 - rank) * SQUARE_SIZE
                        dragging_offset = (mouse_x - square_x, mouse_y - square_y)
                        dragging_pos = event.pos

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    dragging_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging:
                    mouse_x, mouse_y = event.pos
                    # If dropped on board area, add/move piece
                    if mouse_x < BOARD_PANEL_WIDTH:
                        file = mouse_x // SQUARE_SIZE
                        rank = 7 - (mouse_y // SQUARE_SIZE)
                        dest_square = chess.square(file, rank)
                        if dragging_source == "board":
                            board.set_piece_at(dest_square, dragging_piece)
                        elif dragging_source == "panel":
                            color, piece_type = dragging_piece
                            board.set_piece_at(dest_square, chess.Piece(piece_type, color))
                    else:
                        # Dropped on right panel: if dragging from board, remove piece.
                        if dragging_source == "board":
                            # Piece is removed; do nothing.
                            pass
                    dragging = False
                    dragging_piece = None
                    dragging_source = None
                    dragging_origin_square = None
                    dragging_pos = None

        # ───────── DRAWING ─────────
        # Clear screen
        screen.fill((0, 0, 0))

        # Draw board (left panel)
        for rank in range(8):
            for file in range(8):
                x = file * SQUARE_SIZE
                y = (7 - rank) * SQUARE_SIZE
                square_rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
                square_color = LIGHT_COLOR if (rank + file) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(screen, square_color, square_rect)

                # Attack visualization: white attackers at top-left, black attackers at top-right.
                square_index = chess.square(file, rank)
                white_attackers = board.attackers(chess.WHITE, square_index)
                black_attackers = board.attackers(chess.BLACK, square_index)
                white_count = len(white_attackers)
                black_count = len(black_attackers)
                if white_count > 0:
                    count_text = str(white_count)
                    pos = (x + MARGIN, y + MARGIN)
                    draw_text_with_outline(screen, count_text, number_font, pos, (255, 255, 255), (0, 0, 0))
                if black_count > 0:
                    count_text = str(black_count)
                    # Now drawn at top-right
                    text_surface = number_font.render(count_text, True, (0, 0, 0))
                    text_rect = text_surface.get_rect()
                    pos = (x + SQUARE_SIZE - text_rect.width - MARGIN, y + MARGIN)
                    draw_text_with_outline(screen, count_text, number_font, pos, (0, 0, 0), (255, 255, 255))

        # Draw board pieces (skip the piece being dragged from board)
        for square in chess.SQUARES:
            if dragging_source == "board" and square == dragging_origin_square:
                continue
            piece = board.piece_at(square)
            if piece:
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                x = file * SQUARE_SIZE
                y = (7 - rank) * SQUARE_SIZE
                symbol = piece_unicode(piece)
                if piece.color == chess.WHITE:
                    piece_color = (255, 255, 255)
                    outline_color = (0, 0, 0)
                else:
                    piece_color = (0, 0, 0)
                    outline_color = (255, 255, 255)
                text_surface = board_piece_font.render(symbol, True, piece_color)
                text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                for dx in (-2, 2):
                    for dy in (-2, 2):
                        outline_surface = board_piece_font.render(symbol, True, outline_color)
                        outline_rect = outline_surface.get_rect(center=(x + SQUARE_SIZE // 2 + dx, y + SQUARE_SIZE // 2 + dy))
                        screen.blit(outline_surface, outline_rect)
                screen.blit(text_surface, text_rect)

        # Draw dragging piece (if any)
        if dragging and dragging_pos:
            draw_x = dragging_pos[0] - dragging_offset[0]
            draw_y = dragging_pos[1] - dragging_offset[1]
            if dragging_source == "panel":
                color, piece_type = dragging_piece
                temp_piece = chess.Piece(piece_type, color)
                symbol = piece_unicode(temp_piece)
                if color == chess.WHITE:
                    piece_color = (255, 255, 255)
                    outline_color = (0, 0, 0)
                else:
                    piece_color = (0, 0, 0)
                    outline_color = (255, 255, 255)
            else:
                symbol = piece_unicode(dragging_piece)
                if dragging_piece.color == chess.WHITE:
                    piece_color = (255, 255, 255)
                    outline_color = (0, 0, 0)
                else:
                    piece_color = (0, 0, 0)
                    outline_color = (255, 255, 255)
            text_surface = board_piece_font.render(symbol, True, piece_color)
            text_rect = text_surface.get_rect(center=(draw_x + SQUARE_SIZE // 2, draw_y + SQUARE_SIZE // 2))
            for dx in (-2, 2):
                for dy in (-2, 2):
                    outline_surface = board_piece_font.render(symbol, True, outline_color)
                    outline_rect = outline_surface.get_rect(center=(draw_x + SQUARE_SIZE // 2 + dx, draw_y + SQUARE_SIZE // 2 + dy))
                    screen.blit(outline_surface, outline_rect)
            screen.blit(text_surface, text_rect)

        # ───────── Draw Right Panel ─────────
        panel_rect = pygame.Rect(BOARD_PANEL_WIDTH, 0, RIGHT_PANEL_WIDTH, TOTAL_HEIGHT)
        pygame.draw.rect(screen, PANEL_BG_COLOR, panel_rect)

        # Draw input boxes
        fen_input.draw(screen)
        pgn_input.draw(screen)

        # Draw buttons with text
        def draw_button(key, label):
            rect = buttons[key]
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_x, mouse_y) else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect)
            btn_font = pygame.font.SysFont("Arial", 16, bold=True)
            txt_surf = btn_font.render(label, True, BUTTON_TEXT_COLOR)
            txt_rect = txt_surf.get_rect(center=rect.center)
            screen.blit(txt_surf, txt_rect)

        draw_button("load_fen", "Load FEN")
        draw_button("export_fen", "Export FEN")
        draw_button("load_pgn", "Load PGN")
        draw_button("export_pgn", "Export PGN")
        draw_button("prev", "Prev")
        draw_button("next", "Next")
        draw_button("lock_toggle", "Lock" if locked else "Unlock")
        draw_button("clear", "Clear")
        draw_button("start", "Start")

        # Draw toolbox piece icons
        for icon in toolbox_icons:
            pygame.draw.rect(screen, (100, 100, 100), icon["rect"], 1)
            symbol = piece_unicode(icon["piece"])
            txt_surf = toolbox_piece_font.render(symbol, True, (0, 0, 0))
            txt_rect = txt_surf.get_rect(center=icon["rect"].center)
            screen.blit(txt_surf, txt_rect)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()