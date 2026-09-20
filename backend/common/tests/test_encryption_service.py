from io import BytesIO
from typing import Tuple

import pytest

from common.services.encryption_service import (
    AES_KEY_LEN_BYTES,
    AES_MAC_LEN,
    FIXED_AES_KEY,
    AESMasterKey,
    FileEncryptionService,
    FileEncryptionServiceException,
)


def test_aes_master_key_init():
    key = AESMasterKey()
    assert key.key.get_secret_value() != b""
    assert len(key.key.get_secret_value()) == AES_KEY_LEN_BYTES


def test_aes_master_key_from_random_source():
    random_source = bytes(AES_KEY_LEN_BYTES)
    key = AESMasterKey.from_random_source(random_source)
    assert key.key.get_secret_value() != b""
    assert len(key.key.get_secret_value()) == AES_KEY_LEN_BYTES


def test_aes_master_key_from_random_source_optional():
    key = AESMasterKey.from_random_source()
    assert key.key.get_secret_value() != b""
    assert len(key.key.get_secret_value()) == AES_KEY_LEN_BYTES


def test_aes_master_key_from_string():
    hex_key = "ab" * AES_KEY_LEN_BYTES
    key = AESMasterKey.from_string(hex_key)
    assert key.key.get_secret_value() == bytes.fromhex(hex_key)
    assert len(key.key.get_secret_value()) == AES_KEY_LEN_BYTES


def test_aes_master_key_from_string_invalid_hex():
    with pytest.raises(ValueError):
        AESMasterKey.from_string("not-valid-hex" + "0" * 51)


def test_aes_master_key_from_string_wrong_length():
    with pytest.raises(ValueError):
        AESMasterKey.from_string("ab" * (AES_KEY_LEN_BYTES - 1))


def test_aes_master_key_from_fixed_key():
    key = AESMasterKey.from_fixed_key()
    assert key.key.get_secret_value() == FIXED_AES_KEY
    assert len(key.key.get_secret_value()) == AES_KEY_LEN_BYTES


def test_aes_master_key_modify():
    key1 = AESMasterKey.from_random_source()
    key2 = AESMasterKey.from_random_source()
    key1.key = key2.key
    assert key1.key.get_secret_value() == key2.key.get_secret_value()
    assert len(key1.key.get_secret_value()) == AES_KEY_LEN_BYTES


def test_aes_master_key_modify_too_short():
    key = AESMasterKey.from_random_source()
    with pytest.raises(ValueError):
        key.key = b""


def test_aes_master_key_modify_too_long():
    key = AESMasterKey.from_random_source()
    with pytest.raises(ValueError):
        key.key = b"x" * (AES_KEY_LEN_BYTES + 1)


_plaintext_chunks = [
    tuple(),
    (b"",),
    (b"Just some random text",),
    (b"small",),
    (b"Very long text" * 10,),
    (b"", b"", b""),
    (b"", b"text", b""),
    (
        b"Just",
        b"Some",
        b"random",
        b"text",
    ),
]


@pytest.mark.parametrize(
    "plaintext_chunks",
    _plaintext_chunks,
)
def test_file_encryption_service_encrypt_decrypt(plaintext_chunks: Tuple[bytes]):
    plaintext = b"".join(plaintext_chunks)
    file_encryption_service = FileEncryptionService()

    encrypted_stream = file_encryption_service.get_encrypted_stream(
        iter(plaintext_chunks)
    )
    encrypted_file = BytesIO(b"".join(encrypted_stream))

    encrypted_file_data = encrypted_file.getvalue()
    assert encrypted_file_data != plaintext
    assert len(encrypted_file_data) > len(plaintext)

    decrypted_stream = file_encryption_service.get_decrypted_stream(
        iter([encrypted_file.read()])
    )
    decrypted_file = b"".join(decrypted_stream)

    assert decrypted_file == plaintext


@pytest.mark.parametrize(
    "plaintext_chunks",
    _plaintext_chunks,
)
def test_file_encryption_service_encrypt_decrypt_all_at_once(
    plaintext_chunks: Tuple[bytes],
):
    plaintext = b"".join(plaintext_chunks)
    file_encryption_service = FileEncryptionService()

    encrypted_stream = file_encryption_service.get_encrypted_stream(iter([plaintext]))
    encrypted_file = BytesIO(b"".join(encrypted_stream))

    encrypted_file_data = encrypted_file.getvalue()
    assert encrypted_file_data != plaintext
    assert len(encrypted_file_data) > len(plaintext)

    decrypted_stream = file_encryption_service.get_decrypted_stream(
        iter([encrypted_file.read()])
    )
    decrypted_file = b"".join(decrypted_stream)

    assert decrypted_file == plaintext


@pytest.mark.parametrize(
    "plaintext_chunks",
    _plaintext_chunks,
)
def test_file_encryption_service_encrypt_decrypt_mac_works(
    plaintext_chunks: Tuple[bytes],
):
    file_encryption_service = FileEncryptionService()

    encrypted_stream = file_encryption_service.get_encrypted_stream(
        iter(plaintext_chunks)
    )
    encrypted_file = BytesIO(b"".join(encrypted_stream))

    # tamper with the data
    encrypted_file_buffer = encrypted_file.getvalue()
    for i, value in enumerate(encrypted_file_buffer):
        modified_encrypted_file_buffer = bytearray(encrypted_file_buffer)
        modified_encrypted_file_buffer[i] = value + 1 if value < 255 else 0
        with pytest.raises((FileEncryptionServiceException, ValueError)):
            decrypted_stream = file_encryption_service.get_decrypted_stream(
                iter([bytes(modified_encrypted_file_buffer)])
            )
            list(decrypted_stream)  # consume generator to trigger MAC verification


def _encrypted(service: FileEncryptionService, plaintext: bytes) -> bytes:
    return b"".join(service.get_encrypted_stream(iter([plaintext])))


def test_decrypt_prefix_matches_what_the_full_decoder_produces():
    """Tie the probe to the real decoder rather than to itself.

    The probe rebuilds the GCM keystream from the header alone. If that ever drifts from
    what `get_decrypted_stream` does, the routing it feeds would quietly start rejecting
    archives this deployment can in fact open.
    """
    service = FileEncryptionService(AESMasterKey())
    plaintext = b"PK\x03\x04" + bytes(range(256)) * 4

    encrypted = _encrypted(service, plaintext)

    assert service.decrypt_prefix(encrypted, 64) == plaintext[:64]
    assert (
        b"".join(service.get_decrypted_stream(iter([encrypted])))[:64] == plaintext[:64]
    )


def test_decrypt_prefix_needs_only_the_header_and_the_bytes_it_returns():
    """The point of the probe: it never sees the tail, where the MAC lives."""
    service = FileEncryptionService(AESMasterKey())
    plaintext = b"PK\x03\x04" + b"x" * 100_000

    encrypted = _encrypted(service, plaintext)
    head = encrypted[: service.header_size + 4]

    assert service.decrypt_prefix(head, 4) == b"PK\x03\x04"


def test_decrypt_prefix_with_the_wrong_key_does_not_return_the_plaintext():
    plaintext = b"PK\x03\x04" + b"payload"

    encrypted = _encrypted(FileEncryptionService(AESMasterKey()), plaintext)

    other = FileEncryptionService(AESMasterKey())
    assert other.decrypt_prefix(encrypted, 4) != b"PK\x03\x04"


def test_decrypt_prefix_returns_none_for_a_head_shorter_than_the_header():
    service = FileEncryptionService(AESMasterKey())

    encrypted = _encrypted(service, b"payload")

    assert service.decrypt_prefix(encrypted[: service.header_size - 1], 4) is None


def test_decrypt_prefix_returns_none_when_the_magic_does_not_match():
    service = FileEncryptionService(AESMasterKey())

    assert service.decrypt_prefix(b"%PDF-1.7" + b"\x00" * 200, 4) is None


def test_decrypt_prefix_returns_what_it_has_when_the_head_runs_out():
    """A truncated object yields a short prefix rather than raising."""
    service = FileEncryptionService(AESMasterKey())

    encrypted = _encrypted(service, b"PK\x03\x04payload")

    assert service.decrypt_prefix(encrypted[: service.header_size + 2], 4) == b"PK"


def test_header_size_agrees_with_what_the_encoder_writes():
    service = FileEncryptionService(AESMasterKey())

    encrypted = _encrypted(service, b"")

    # magic + salt + nonce, then nothing but the MAC for empty plaintext.
    assert len(encrypted) == service.header_size + AES_MAC_LEN
