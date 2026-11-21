from chess import BISHOP, COLORS, KNIGHT, PAWN, QUEEN, ROOK


MaximumHalfmoveClock: Final[int] = 32767
MaximumFullmoveNumber: Final[int] = 100_000
InitialPieceCounts: Final[dict[PieceType, int]] = {KNIGHT: 2, BISHOP: 2, ROOK: 2, QUEEN: 1}


def is_valid_position(position: Board) -> bool:
    """Return True if `position` is valid and supported by engines."""
    if position.uci_variant != "chess" or position.chess960:
        return False

    if not position.is_valid():
        return False

    if position.halfmove_clock > MaximumHalfmoveClock:
        return False

    if position.fullmove_number > MaximumFullmoveNumber:
        return False

    for color in COLORS:
        missing_pawns: int = 8 - len(position.pieces(PAWN, color))

        if _promoted_pieces(position, color) > missing_pawns:
            return False

    return True


def _promoted_pieces(position: Board, color: Color) -> int:
    """Get promoted piece count for `color` in `position`."""
    promoted_pieces: int = 0

    for piece_type, initial_count in InitialPieceCounts.items():
        piece_count: int = len(position.pieces(piece_type, color))

        if piece_count > initial_count:
            promoted_pieces += piece_count - initial_count

    return promoted_pieces
