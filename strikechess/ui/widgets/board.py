from chess import Piece, square, svg
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
    Slot,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QSizePolicy


AnimationDurationMilliseconds: Final[int] = 350
Expanding: Final[QSizePolicy.Policy] = QSizePolicy.Policy.Expanding

svg.XX = "<circle id='xx' r='4.5' cx='22.5' cy='22.5' stroke='#303030' fill='#e5e5e5'/>"


def _create_color(attribute_name: str) -> Property:
    """Create QColor property for board theme."""
    return Property(
        QColor,
        lambda self: getattr(self, attribute_name),
        lambda self, color: setattr(self, attribute_name, color),
    )


class SvgBoard(QSvgWidget):
    """Scalable Vector Graphics (SVG) board with drag-and-drop."""

    coord = _create_color("_coord")
    margin = _create_color("_margin")
    square_dark = _create_color("_square_dark")
    inner_border = _create_color("_inner_border")
    outer_border = _create_color("_outer_border")
    square_light = _create_color("_square_light")
    square_dark_lastmove = _create_color("_square_dark_lastmove")
    square_light_lastmove = _create_color("_square_light_lastmove")

    def __init__(self, game: GameService, settings: SettingsService) -> None:
        super().__init__()

        self._game: GameService = game
        self._settings: SettingsService = settings

        self.is_dragging: bool = False
        self.is_animating: bool = False
        self.is_interactive: bool = True
        self.dragged_piece: Piece | None = None
        self.animated_piece: Piece | None = None
        self.origin_square: Square | None = None
        self.cursor_point: QPointF = QPointF(0.0, 0.0)
        self.animation_point: QPointF = QPointF(0.0, 0.0)
        self.is_white_at_bottom: bool = self._settings.value("ui", "is_white_at_bottom")

        self._coord: QColor = QColor()
        self._margin: QColor = QColor()
        self._square_dark: QColor = QColor()
        self._inner_border: QColor = QColor()
        self._outer_border: QColor = QColor()
        self._square_light: QColor = QColor()
        self._square_dark_lastmove: QColor = QColor()
        self._square_light_lastmove: QColor = QColor()

        self._animation: QVariantAnimation = QVariantAnimation(self)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.setDuration(AnimationDurationMilliseconds)
        self._animation.valueChanged.connect(self.update_animation_point)
        self._animation.finished.connect(self.stop_dragging)

        size_policy: QSizePolicy = QSizePolicy(Expanding, Expanding)
        size_policy.setHeightForWidth(True)
        self.setSizePolicy(size_policy)

        self.setMouseTracking(True)

    def sizeHint(self) -> QSize:
        """Get preferred board size."""
        return QSize(500, 500)

    def minimumSizeHint(self) -> QSize:
        """Get minimum board size."""
        return QSize(400, 400)

    def heightForWidth(self, width: int) -> int:
        """Get required height based on `width` to keep square shape."""
        return width

    @property
    def board_size(self) -> int:
        """Board size in pixels."""
        return self.width()

    @property
    def board_margin(self) -> float:
        """Board margin based on board size."""
        board_margin_percentage: float = 0.04
        return self.board_size * board_margin_percentage

    @property
    def square_size(self) -> float:
        """Square size based on board size."""
        squares_per_row: int = 8
        return (self.board_size - 2 * self.board_margin) / squares_per_row

    @property
    def half_square_size(self) -> float:
        """Half of square size."""
        return self.square_size / 2

    @property
    def square_center_offset(self) -> float:
        """Offset to square center, accounting for board margin."""
        return self.half_square_size + self.board_margin

    def enable_interaction(self) -> None:
        """Allow human to play moves."""
        self.is_interactive = True

    def disable_interaction(self) -> None:
        """Prevent human from playing moves."""
        self.is_interactive = False
        self.stop_dragging()

    def set_orientation(self, is_white_at_bottom: bool) -> None:
        """Set board orientation based on `is_white_at_bottom`."""
        self.is_white_at_bottom = is_white_at_bottom

    def color_names(self) -> dict[str, str]:
        """Get color names for SVG rendering."""
        return {
            "coord": self._coord.name(),
            "inner border": self._inner_border.name(),
            "margin": self._margin.name(),
            "outer border": self._outer_border.name(),
            "square dark": self._square_dark.name(),
            "square dark lastmove": self._square_dark_lastmove.name(),
            "square light": self._square_light.name(),
            "square light lastmove": self._square_light_lastmove.name(),
        }

    def square_center(self, square: Square) -> QPointF:
        """Get center point of `square`."""
        file: int = square % 8
        rank: int = square // 8

        if self.is_white_at_bottom:
            flipped_rank: int = 7 - rank
            x: float = self.square_center_offset + (self.square_size * file)
            y: float = self.square_center_offset + (self.square_size * flipped_rank)
        else:
            flipped_file: int = 7 - file
            x = self.square_center_offset + (self.square_size * flipped_file)
            y = self.square_center_offset + (self.square_size * rank)

        return QPointF(x, y)

    def square(self, cursor_point: QPointF) -> Square:
        """Get square based on `cursor_point`."""
        if self.is_white_at_bottom:
            file: float = (cursor_point.x() - self.board_margin) // self.square_size
            rank: float = 7 - (cursor_point.y() - self.board_margin) // self.square_size
        else:
            file = 7 - (cursor_point.x() - self.board_margin) // self.square_size
            rank = (cursor_point.y() - self.board_margin) // self.square_size

        file_index: int = max(0, min(7, round(file)))
        rank_index: int = max(0, min(7, round(rank)))
        return square(file_index, rank_index)

    def cursor_point_from(self, event: QMouseEvent) -> QPointF:
        """Get cursor point from position data of `event`."""
        self.cursor_point = event.position()
        return self.cursor_point

    def can_drag(self, piece: Piece | None) -> bool:
        """Return True if `piece` can be dragged."""
        if piece is None or not self.is_interactive:
            return False

        is_engine_loaded: bool = self._settings.value("engine", "name") != "(no engine)"
        is_engine_piece: bool = piece.color == self._settings.value("engine", "is_white")

        if is_engine_loaded and is_engine_piece:
            return False

        return True

    def is_legal(self, target_square: Square) -> bool:
        """Return True if dropping piece at `target_square` is legal."""
        legal_target_squares: list[Square] = self._game.legal_target_squares(self.origin_square)
        return target_square in legal_target_squares

    def update_cursor_at(self, cursor_point: QPointF) -> None:
        """Update cursor based on draggability at `cursor_point`."""
        square: Square = self.square(cursor_point)
        piece: Piece | None = self._game.piece_at(square)

        if self.is_dragging:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if piece is not None and self.can_drag(piece):
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            return

        self.unsetCursor()

    def start_dragging(self, square: Square, piece: Piece) -> None:
        """Start dragging `piece` from `square`."""
        self.is_dragging = True
        self.dragged_piece = piece
        self.origin_square = square
        self._game.origin_square = square

        self.update_cursor_at(self.cursor_point)

    def drop_piece(self, target_square: Square) -> None:
        """Drop dragged piece at `target_square`."""
        self._game.target_square = target_square
        self._game.find_legal_move(self.origin_square, target_square)

        self.stop_dragging()

    def slide_piece_back(self, cursor_point: QPointF) -> None:
        """Slide dragged piece from `cursor_point` back to origin."""
        self.is_dragging = False

        if self.origin_square is not None and self.dragged_piece is not None:
            self.animate_piece(
                cursor_point=cursor_point,
                origin_square=self.origin_square,
                dragged_piece=self.dragged_piece,
            )

        self.update_cursor_at(cursor_point)

    def animate_piece(
        self,
        cursor_point: QPointF,
        origin_square: Square,
        dragged_piece: Piece,
    ) -> None:
        """Animate sliding `dragged_piece` back to `origin_square`."""
        self.is_animating = True
        self.animated_piece = dragged_piece
        self.origin_square = origin_square

        self.animation_point = cursor_point

        self._animation.setStartValue(cursor_point)
        self._animation.setEndValue(self.square_center(origin_square))
        self._animation.start()

    @Slot(QPointF)
    def update_animation_point(self, point: QPointF) -> None:
        """Update animated piece position based on `point`."""
        self.animation_point = point

    @Slot()
    def stop_dragging(self) -> None:
        """Reset dragging-related state."""
        self.is_dragging = False
        self.is_animating = False
        self.dragged_piece = None
        self.origin_square = None
        self.animated_piece = None

        self.update_cursor_at(self.cursor_point)

    def svg_data(self) -> bytes:
        """Convert current board state to SVG data as bytes."""
        board_to_render: Board = self._game.board

        if self.origin_square is not None and (self.is_dragging or self.is_animating):
            board_to_render = board_to_render.copy()
            board_to_render.set_piece_at(square=self.origin_square, piece=None)

        square: Square | None = self.origin_square if self.is_dragging else None
        legal_target_squares: list[Square] = self._game.legal_target_squares(square)

        svg_board: str = svg.board(
            board=board_to_render,
            squares=legal_target_squares,
            check=self._game.check,
            arrows=self._game.arrow,
            colors=self.color_names(),
            orientation=self.is_white_at_bottom,
        )
        return svg_board.encode()

    def svg_renderer(self, piece_symbol: str) -> QSvgRenderer:
        """Create SVG renderer for piece based on `piece_symbol`."""
        svg_piece: str = svg.piece(Piece.from_symbol(piece_symbol))
        renderer: QSvgRenderer = QSvgRenderer()
        renderer.load(svg_piece.encode())
        return renderer

    def piece_render_area_at(self, cursor_point: QPointF) -> QRectF:
        """Get piece render area centered at `cursor_point`."""
        render_area: QRectF = QRectF(0, 0, self.square_size, self.square_size)
        render_area.moveCenter(cursor_point)
        return render_area

    def render_piece(self, cursor_point: QPointF, piece: Piece | None = None) -> None:
        """Render either dragged piece or `piece` at `cursor_point`."""
        piece_to_render: Piece | None = self.dragged_piece or piece

        if piece_to_render is None:
            return

        painter: QPainter = QPainter(self)
        piece_symbol: str = piece_to_render.symbol()
        renderer: QSvgRenderer = self.svg_renderer(piece_symbol)
        piece_render_area: QRectF = self.piece_render_area_at(cursor_point)
        renderer.render(painter, piece_render_area)
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Drag piece if draggable."""
        if self.is_animating or not self.is_interactive:
            return

        cursor_point: QPointF = self.cursor_point_from(event)
        square: Square = self.square(cursor_point)
        piece: Piece | None = self._game.piece_at(square)

        if piece is not None and self.can_drag(piece):
            self.start_dragging(square, piece)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Update cursor based on hovered piece."""
        cursor_point: QPointF = self.cursor_point_from(event)
        self.update_cursor_at(cursor_point)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Drop piece if legal move, else slide it back."""
        cursor_point: QPointF = self.cursor_point_from(event)
        square: Square = self.square(cursor_point)

        if self.is_legal(square):
            self.drop_piece(square)
        else:
            self.slide_piece_back(cursor_point)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render board and any dragged or animated piece."""
        board_svg: bytes = self.svg_data()
        self.load(board_svg)
        super().paintEvent(event)

        if self.is_dragging and self.dragged_piece is not None:
            current_piece: Piece | None = self._game.piece_at(self.origin_square)

            if current_piece is not None and current_piece.color != self.dragged_piece.color:
                self.stop_dragging()
            else:
                self.render_piece(self.cursor_point)

        if self.is_animating:
            self.render_piece(self.animation_point, self.animated_piece)
