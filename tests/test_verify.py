"""Tests for independent MAYO signature verification."""

from typing import cast

import pytest

import scheme.verify as verify_module

from crypto.hashing import derive_key_material
from keys.expand_public import expand_public_key, generate_P1_P2
from keys.expand_secret import decode_O, expand_secret_key
from keys.keygen import compute_P3, encode_P3
from keys.parameters import (
    O_DIM,
    SEED_PK_BYTES,
    SEED_SK_BYTES,
    V,
)
from scheme.sign import sign
from scheme.verify import verify


def _compact_public_key(seed_sk: bytes) -> bytes:
    """Build a compact public key deterministically from a secret seed."""
    seed_pk, encoded_O = derive_key_material(
        seed_sk,
        SEED_SK_BYTES,
        SEED_PK_BYTES,
        V,
        O_DIM,
    )
    O = decode_O(encoded_O)
    P1, P2 = generate_P1_P2(seed_pk)
    return seed_pk + encode_P3(compute_P3(O, P1, P2))


@pytest.fixture(scope="module")
def signed_message() -> tuple[bytes, bytes, bytes, bytes]:
    """Prepare a deterministic key pair and one valid signature."""
    seed_sk = bytes(range(SEED_SK_BYTES))
    cpk = _compact_public_key(seed_sk)
    epk = expand_public_key(cpk)
    esk = expand_secret_key(seed_sk)
    message = b"independent MAYO verification test"
    return epk, esk, message, sign(esk, message)


def test_valid_signature_is_accepted(
    signed_message: tuple[bytes, bytes, bytes, bytes],
) -> None:
    """Verify accepts a signature generated for the original message."""
    epk, _, message, signature = signed_message
    assert len(signature) == 321
    assert verify(epk, message, signature) == 0


def test_modified_message_is_rejected(
    signed_message: tuple[bytes, bytes, bytes, bytes],
) -> None:
    """Verify rejects the same signature for a changed message."""
    epk, _, message, signature = signed_message
    assert verify(epk, message + b"!", signature) == -1


def test_modified_signature_is_rejected(
    signed_message: tuple[bytes, bytes, bytes, bytes],
) -> None:
    """Verify rejects tampered signature bytes."""
    epk, _, message, signature = signed_message
    damaged = bytearray(signature)
    damaged[10] ^= 1
    assert verify(epk, message, bytes(damaged)) == -1


def test_modified_salt_is_rejected(
    signed_message: tuple[bytes, bytes, bytes, bytes],
) -> None:
    """Verify rejects a signature with a modified salt."""
    epk, _, message, signature = signed_message
    damaged = bytearray(signature)
    damaged[-1] ^= 1
    assert verify(epk, message, bytes(damaged)) == -1


def test_other_public_key_is_rejected(
    signed_message: tuple[bytes, bytes, bytes, bytes],
) -> None:
    """Verify rejects a signature checked against another public key."""
    _, _, message, signature = signed_message
    other_seed = bytes(reversed(range(SEED_SK_BYTES)))
    other_epk = expand_public_key(_compact_public_key(other_seed))
    assert verify(other_epk, message, signature) == -1


def test_malformed_signature_and_key_are_rejected(
    signed_message: tuple[bytes, bytes, bytes, bytes],
) -> None:
    """Malformed lengths and key encodings return the invalid-signature result."""
    epk, _, message, signature = signed_message
    assert verify(epk, message, b"") == -1
    assert verify(b"", message, b"bad") == -1
    assert verify(epk, message, signature[:-1]) == -1
    assert verify(epk, message, signature + b"\x00") == -1
    assert verify(epk + b"\x00", message, signature) == -1


@pytest.mark.parametrize(
    ("epk", "message", "signature"),
    [
        (None, b"message", b"signature"),
        (b"epk", None, b"signature"),
        (b"epk", b"message", None),
        (b"epk", 123, b"signature"),
        (bytearray(b"epk"), b"message", b"signature"),
    ],
)
def test_malformed_argument_types_are_rejected(
    epk: object,
    message: object,
    signature: object,
) -> None:
    """Verify rejects inputs that do not match its public argument types."""
    assert verify(
        cast(bytes, epk),
        cast(bytes | str, message),
        cast(bytes, signature),
    ) == -1


def test_unencodable_message_is_rejected(
    signed_message: tuple[bytes, bytes, bytes, bytes],
) -> None:
    """Verify returns the invalid-signature result for invalid UTF-8 text."""
    epk, _, _, signature = signed_message
    assert verify(epk, "\ud800", signature) == -1


def test_unexpected_internal_error_is_not_swallowed(
    signed_message: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected failures in public-key parsing remain visible to callers."""
    epk, _, message, signature = signed_message

    def raise_internal_error(_: bytes) -> None:
        raise RuntimeError("unexpected parser failure")

    monkeypatch.setattr(verify_module, "parse_epk", raise_internal_error)
    with pytest.raises(RuntimeError, match="unexpected parser failure"):
        verify(epk, message, signature)
