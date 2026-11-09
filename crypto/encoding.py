"""Encoding and decoding helpers for GF(16) elements and vectors."""

from core.field import FIELD_SIZE


def decode_nibbles(data: bytes) -> list[int]:
    """Decode each byte into low-nibble then high-nibble field elements.

    Args:
        data: Bytes containing two packed GF(16) elements per byte.

    Returns:
        The unpacked elements in the existing low-then-high order.
    """
    elements = []
    for byte in data:
        elements.append(byte & 0x0F)
        elements.append((byte >> 4) & 0x0F)
    return elements


def encode_nibbles(elements: list[int]) -> bytes:
    """Pack GF(16) elements two per byte, low nibble first.

    An odd final element is packed with a zero high nibble, matching the
    existing key and signature encoding convention.

    Args:
        elements: Field elements to encode.

    Returns:
        The packed byte representation.

    Raises:
        ValueError: If any element is outside GF(16).
    """
    encoded = bytearray()

    for index in range(0, len(elements), 2):
        low = elements[index]
        if not 0 <= low < FIELD_SIZE:
            raise ValueError("Element invalide dans F16")

        if index + 1 < len(elements):
            high = elements[index + 1]
            if not 0 <= high < FIELD_SIZE:
                raise ValueError("Element invalide dans F16")
        else:
            high = 0

        encoded.append(low | (high << 4))

    return bytes(encoded)


def decode_vector(dim: int, data: bytes) -> list[int]:
    """Decode the first ``dim`` GF(16) elements from packed bytes.

    Extra decoded elements are ignored, as in the original signing module.

    Args:
        dim: Number of elements in the requested vector.
        data: Packed vector bytes.

    Returns:
        A vector containing ``dim`` field elements.

    Raises:
        ValueError: If the input does not contain enough elements.
    """
    elements = decode_nibbles(data)
    if len(elements) < dim:
        raise ValueError("Données insuffisantes pour décoder le vecteur")
    return elements[:dim]


def encode_vector(vector: list[int]) -> bytes:
    """Encode a vector of GF(16) elements in the existing nibble format.

    Args:
        vector: Field elements to pack.

    Returns:
        The low-nibble-first packed bytes.

    Raises:
        ValueError: If a vector element is outside GF(16).
    """
    for value in vector:
        if not 0 <= value < FIELD_SIZE:
            raise ValueError("Élément invalide dans F16 pour l'encodage du vecteur")
    return encode_nibbles(vector)


def _matrix_coordinates(
    rows: int,
    cols: int,
    triangular: bool,
) -> list[tuple[int, int]]:
    if rows < 0 or cols < 0:
        raise ValueError("Les dimensions des matrices ne peuvent pas etre negatives")
    if triangular and rows != cols:
        raise ValueError("Une matrice triangulaire doit être carree")

    return [
        (row, col)
        for row in range(rows)
        for col in range(cols)
        if not triangular or row <= col
    ]


def encode_matrices(
    matrices: list[list[list[int]]],
    rows: int,
    cols: int,
    *,
    triangular: bool = False,
) -> bytes:
    """Encode a sequence of matrices using MAYO's ``EncodeMatrices`` order.

    For each matrix coordinate in row-major order, the corresponding values
    from all matrices are encoded as one vector. Lower-triangular coordinates
    are omitted when ``triangular`` is true.

    Args:
        matrices: Matrices in sequence order.
        rows: Number of rows in each matrix.
        cols: Number of columns in each matrix.
        triangular: Whether to encode only upper-triangular coordinates.

    Returns:
        The nibble-sliced byte representation of the matrix sequence.

    Raises:
        ValueError: If dimensions, matrix shapes, or encoded field elements
            are invalid.
    """
    coordinates = _matrix_coordinates(rows, cols, triangular)
    if not matrices:
        raise ValueError("La sequence de matrices ne peut pas etre vide")

    for matrix in matrices:
        if len(matrix) != rows or any(len(row) != cols for row in matrix):
            raise ValueError("Dimensions incorrectes pour une matrice")

    encoded = bytearray()
    for row, col in coordinates:
        encoded.extend(
            encode_vector([matrix[row][col] for matrix in matrices])
        )

    return bytes(encoded)


def decode_matrices(
    data: bytes,
    matrix_count: int,
    rows: int,
    cols: int,
    *,
    triangular: bool = False,
) -> list[list[list[int]]]:
    """Decode a MAYO ``EncodeMatrices`` byte string.

    The encoded vector for each matrix coordinate occupies its own
    ``ceil(matrix_count / 2)``-byte segment, including its own zero padding
    nibble when ``matrix_count`` is odd.

    Args:
        data: Nibble-sliced matrix-sequence bytes.
        matrix_count: Number of matrices in the sequence.
        rows: Number of rows in each matrix.
        cols: Number of columns in each matrix.
        triangular: Whether only upper-triangular coordinates are encoded.

    Returns:
        The decoded matrices in sequence order. Omitted lower-triangular
        coordinates are zero.

    Raises:
        ValueError: If the count, dimensions, or byte length is invalid.
    """
    if matrix_count <= 0:
        raise ValueError("Le nombre de matrices doit etre positif")

    coordinates = _matrix_coordinates(rows, cols, triangular)
    bytes_per_coordinate = (matrix_count + 1) // 2
    expected_length = len(coordinates) * bytes_per_coordinate
    if len(data) != expected_length:
        raise ValueError(
            f"Taille incorrecte des donnees ({len(data)} != {expected_length})"
        )

    matrices = [
        [[0] * cols for _ in range(rows)]
        for _ in range(matrix_count)
    ]
    position = 0
    for row, col in coordinates:
        values = decode_vector(
            matrix_count,
            data[position:position + bytes_per_coordinate],
        )
        for matrix_index, value in enumerate(values):
            matrices[matrix_index][row][col] = value
        position += bytes_per_coordinate

    return matrices
