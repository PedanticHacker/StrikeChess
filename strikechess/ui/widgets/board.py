from __future__ import annotations

from enum import IntEnum
from functools import lru_cache
from typing import Final, Literal, NamedTuple

from chess import Move, Piece, square, svg
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    Slot,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget

from strikechess.utils import setting_value


svg.XX = "<circle id='xx' r='4.5' cx='22.5' cy='22.5' stroke='#303030' fill='#e5e5e5'/>"


class BoardSize(IntEnum):
    small = 380
    normal = 480
    big = 580


class BoardCache(NamedTuple):
    """Type annotations for board cache."""

    fen: str
    dragging: bool
    orientation: bool
    check: Square | None
    square: Square | None
    arrow: tuple[tuple[Square, Square]]


class SvgBoard(QSvgWidget):
    """Piece drag-and-drop functionality and animation on SVG board."""

    coord: Property = Property(
        QColor,
        lambda self: self._coord,
        lambda self, color: self.update_color("_coord", color),
    )
    inner_border: Property = Property(
        QColor,
        lambda self: self._inner_border,
        lambda self, color: self.update_color("_inner_border", color),
    )
    margin: Property = Property(
        QColor,
        lambda self: self._margin,
        lambda self, color: self.update_color("_margin", color),
    )
    outer_border: Property = Property(
        QColor,
        lambda self: self._outer_border,
        lambda self, color: self.update_color("_outer_border", color),
    )
    square_dark: Property = Property(
        QColor,
        lambda self: self._square_dark,
        lambda self, color: self.update_color("_square_dark", color),
    )
    square_dark_lastmove: Property = Property(
        QColor,
        lambda self: self._square_dark_lastmove,
        lambda self, color: self.update_color("_square_dark_lastmove", color),
    )
    square_light: Property = Property(
        QColor,
        lambda self: self._square_light,
        lambda self, color: self.update_color("_square_light", color),
    )
    square_light_lastmove: Property = Property(
        QColor,
        lambda self: self._square_light_lastmove,
        lambda self, color: self.update_color("_square_light_lastmove", color),
    )

    point: Property = Property(
        QPointF,
        lambda self: self.animation_point,
        lambda self, value: self.set_animation_point(value),
    )

    def __init__(self, game: Game) -> None:
        super().__init__()

        self._game: Game = game

        self.is_dragging: bool = False
        self.is_animating: bool = False
        self.is_interactive: bool = True
        self.dragged_piece: Piece | None = None
        self.animated_piece: Piece | None = None
        self.origin_square: Square | None = None
        self.cursor_point: QPointF = QPointF(0.0, 0.0)
        self.animation_point: QPointF = QPointF(0.0, 0.0)
        self.orientation: bool = setting_value("board", "orientation")

        self._coord: QColor = QColor()
        self._inner_border: QColor = QColor()
        self._margin: QColor = QColor()
        self._outer_border: QColor = QColor()
        self._square_dark: QColor = QColor()
        self._square_dark_lastmove: QColor = QColor()
        self._square_light: QColor = QColor()
        self._square_light_lastmove: QColor = QColor()

        self._animation: QPropertyAnimation = QPropertyAnimation(self, b"point")
        self._animation.setDuration(350)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.finished.connect(self.on_animation_finished)

        self.setMouseTracking(True)

    @property
    def board_size(self) -> int:
        """Get board size based on option in settings."""
        option: Literal["small", "normal", "big"] = setting_value("board", "size")
        return BoardSize[option]

    @property
    def board_margin(self) -> float:
        """Get board margin based on board size."""
        BOARD_MARGIN_FACTOR: Final[float] = 0.04
        return self.board_size * BOARD_MARGIN_FACTOR

    @property
    def square_size(self) -> float:
        """Get square size based on board size."""
        return (self.board_size - 2 * self.board_margin) / 8

    @property
    def half_square_size(self) -> float:
        """Get half size of square."""
        return self.square_size / 2

    @property
    def square_center_offset(self) -> float:
        """Get offset for square center in size of board margin."""
        return self.half_square_size + self.board_margin

    def update_board_size(self) -> None:
        """Update board size and clear caches."""
        self.setFixedSize(self.board_size, self.board_size)

        self.clear_cache()

    def disable_interaction(self):
        """Prevent player from making moves."""
        self.is_interactive = False

        self.stop_dragging()

    def enable_interaction(self):
        """Allow player to make moves."""
        self.is_interactive = True

        self.unsetCursor()
        self.update()

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

    def update_color(self, property_name: str, color_value: QColor) -> None:
        """Update color based on `property_name` and `color_value`."""
        setattr(self, property_name, color_value)

        self.clear_cache()

    def update_orientation(self, orientation: bool) -> None:
        """Update board orientation based on `orientation`."""
        self.orientation = orientation

        self.clear_cache()

    def clear_cache(self) -> None:
        """Clear SVG data and renderer caches, then update board."""
        self.svg_data.cache_clear()
        self.svg_renderer.cache_clear()

        self.update()

    def board_cache(self) -> BoardCache:
        """Get cache of current board state."""
        return BoardCache(
            fen=self._game.fen,
            check=self._game.check,
            dragging=self.is_dragging,
            square=self.origin_square,
            orientation=self.orientation,
            arrow=tuple(self._game.arrow),
        )

    def set_animation_point(self, value: QPointF) -> None:
        """Set animation point based on `value`."""
        self.animation_point = value

    def square_center(self, square: Square) -> QPointF:
        """Get center point of `square`."""
        file: int = square % 8
        rank: int = square // 8

        if self.orientation:
            flipped_rank: int = 7 - rank
            x: float = self.square_center_offset + (self.square_size * file)
            y: float = self.square_center_offset + (self.square_size * flipped_rank)
        else:
            flipped_file: int = 7 - file
            x = self.square_center_offset + (self.square_size * flipped_file)
            y = self.square_center_offset + (self.square_size * rank)

        return QPointF(x, y)

    def square_index(self, cursor_point: QPointF) -> Square:
        """Get square index based on `cursor_point`."""
        if self.orientation:
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
        """Return True if `piece` does not belong to engine."""
        return (
            piece is not None
            and piece.color != setting_value("engine", "is_white")
            and self.is_interactive
        )

    def is_legal(self, target_square: Square) -> bool:
        """Return True if `target_square` is legal for dragged piece."""
        legal_targets: list[Square] = self._game.legal_targets(self.origin_square)
        return target_square in legal_targets

    def update_cursor_shape_at(self, cursor_point: QPointF) -> None:
        """Update cursor shape at `cursor_point`."""
        square_index: Square = self.square_index(cursor_point)
        piece: Piece | None = self._game.piece_at(square_index)

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

        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.update()

    def stop_dragging(self) -> None:
        """Stop piece dragging and reset dragging-related state."""
        self._game.reset_selected_squares()

        self.is_dragging = False
        self.is_animating = False
        self.dragged_piece = None
        self.origin_square = None
        self.animated_piece = None

        self.unsetCursor()
        self.update()

    def drop_piece(self, target_square: Square) -> None:
        """Drop dragged piece onto `target_square`."""
        self._game.target_square = target_square
        self._game.find_legal_move(self.origin_square, target_square)

        self.stop_dragging()

    def return_piece_at(self, cursor_point: QPointF) -> None:
        """Return dragged piece at `cursor_point` to origin square."""
        self.is_dragging = False

        if self.origin_square is not None and self.dragged_piece is not None:
            self.start_animation(
                cursor_point=cursor_point,
                origin_square=self.origin_square,
                dragged_piece=self.dragged_piece,
            )

        self.unsetCursor()

    def start_animation(
        self,
        cursor_point: QPointF,
        origin_square: Square,
        dragged_piece: Piece,
    ) -> None:
        """Animate returning `dragged_piece` to `origin_square`."""
        self.is_animating = True
        self.animated_piece = dragged_piece
        self.origin_square = origin_square

        self._animation_point = cursor_point
        self._animation.setStartValue(cursor_point)
        self._animation.setEndValue(self.square_center(origin_square))
        self._animation.start()

    @lru_cache(maxsize=128)
    def svg_data(self, cache: BoardCache) -> bytes:
        """Transform current board state into SVG data as bytes."""
        board_to_render: Board = self._game.board

        if cache.square is not None and cache.dragging or self.is_animating:
            square: Square | None = (
                cache.square if cache.dragging else self.origin_square
            )
            board_to_render = board_to_render.copy()
            board_to_render.set_piece_at(square=square, piece=None)

        cached_square: Square | None = cache.square if cache.dragging else None
        legal_targets: list[Square] = self._game.legal_targets(cached_square)

        svg_board: str = svg.board(
            check=cache.check,
            arrows=cache.arrow,
            board=board_to_render,
            squares=legal_targets,
            colors=self.color_names(),
            orientation=cache.orientation,
        )
        return svg_board.encode()

    @lru_cache(maxsize=12)
    def svg_renderer(self, piece_symbol: str) -> QSvgRenderer:
        """Get or create piece SVG renderer based on `piece_symbol`."""
        svg_piece: str = svg.piece(Piece.from_symbol(piece_symbol))
        renderer: QSvgRenderer = QSvgRenderer()
        renderer.load(svg_piece.encode())
        return renderer

    def piece_render_area_at(self, cursor_point: QPointF) -> QRectF:
        """Get piece render area based on `cursor_point`."""
        return QRectF(
            cursor_point.x() - self.half_square_size,
            cursor_point.y() - self.half_square_size,
            self.square_size,
            self.square_size,
        )

    def render_piece(
        self,
        cursor_point: QPointF,
        piece: Piece | None = None,
    ) -> None:
        """Render `piece` at `cursor_point`."""
        dragged_piece: Piece | None = self.dragged_piece or None
        piece_to_render: Piece | None = dragged_piece or piece

        if piece_to_render is None:
            return

        painter: QPainter = QPainter(self)
        piece_symbol: str = piece_to_render.symbol()
        renderer: QSvgRenderer = self.svg_renderer(piece_symbol)
        piece_render_area: QRectF = self.piece_render_area_at(cursor_point)
        renderer.render(painter, piece_render_area)
        painter.end()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render board and piece to animate."""
        board_svg: bytes = self.svg_data(self.board_cache())
        self.load(board_svg)
        super().paintEvent(event)

        if self.is_dragging and self.dragged_piece is not None:
            current_piece: Piece = self._game.piece_at(self.origin_square)

            if current_piece.color != self.dragged_piece.color:
                self.stop_dragging()
            else:
                self.render_piece(self.cursor_point)

        if self.is_animating:
            self.render_piece(self.animation_point, self.animated_piece)

    def select_square_at(self, cursor_point: QPointF) -> None:
        """Select square at `cursor_point`."""
        square_index: Square = self.square_index(cursor_point)
        self._game.set_selected_square(square_index)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for piece selection or targeting."""
        if self._game.is_over() or not self.is_interactive:
            return

        cursor_point: QPointF = self.cursor_point_from(event)
        square_index: Square = self.square_index(cursor_point)
        piece: Piece | None = self._game.piece_at(square_index)

        if piece is not None and self.can_drag(piece):
            self.start_dragging(square_index, piece)
        else:
            self.select_square_at(cursor_point)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Update cursor shape when hovering over board."""
        cursor_point: QPointF = self.cursor_point_from(event)
        self.update_cursor_shape_at(cursor_point)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Make move with dragging piece or return it back."""
        cursor_point: QPointF = self.cursor_point_from(event)
        square_index: Square = self.square_index(cursor_point)

        if self.is_legal(square_index):
            self.drop_piece(square_index)
        else:
            self.return_piece_at(cursor_point)

    @Slot()
    def on_animation_finished(self) -> None:
        """Reset board state after animation has finished."""
        self.stop_dragging()
