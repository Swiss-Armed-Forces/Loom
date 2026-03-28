from io import BytesIO
from typing import Tuple

import pytest

from common.services.encryption_service import (
    AES_KEY_LEN_BYTES,
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
