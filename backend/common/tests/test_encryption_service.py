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
    encrypted_file = BytesIO()

    with file_encryption_service.get_encryptor(encrypted_file) as encrypt:
        for plaintext_chunk in plaintext_chunks:
            encrypt(plaintext_chunk)
    encrypted_file.seek(0)

    encrypted_file_data = encrypted_file.getvalue()
    assert encrypted_file_data != plaintext
    assert len(encrypted_file_data) > len(plaintext)

    decrypted_file = b""
    with file_encryption_service.get_decryptor(encrypted_file) as decrypt:
        for plaintext_chunk in plaintext_chunks:
            decrypted_file_chunk = decrypt(len(plaintext_chunk))
            assert decrypted_file_chunk == plaintext_chunk
            decrypted_file += decrypted_file_chunk

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
    encrypted_file = BytesIO()

    with file_encryption_service.get_encryptor(encrypted_file) as encrypt:
        encrypt(plaintext)
    encrypted_file.seek(0)

    encrypted_file_data = encrypted_file.getvalue()
    assert encrypted_file_data != plaintext
    assert len(encrypted_file_data) > len(plaintext)

    decrypted_file = b""
    with file_encryption_service.get_decryptor(encrypted_file) as decrypt:
        decrypted_file = decrypt()

    assert decrypted_file == plaintext


@pytest.mark.parametrize(
    "plaintext_chunks",
    _plaintext_chunks,
)
def test_file_encryption_service_encrypt_decrypt_mac_works(
    plaintext_chunks: Tuple[bytes],
):
    file_encryption_service = FileEncryptionService()
    encrypted_file = BytesIO()

    with file_encryption_service.get_encryptor(encrypted_file) as encrypt:
        for plaintext_chunk in plaintext_chunks:
            encrypt(plaintext_chunk)
    encrypted_file.seek(0)

    # tamper with the data
    encrypted_file_buffer = encrypted_file.getvalue()
    for i, value in enumerate(encrypted_file_buffer):
        modified_encrypted_file_buffer = BytesIO(encrypted_file_buffer)
        modified_encrypted_file_buffer.getbuffer()[i] = value + 1 if value < 255 else 0
        with pytest.raises((FileEncryptionServiceException, ValueError)):
            with file_encryption_service.get_decryptor(
                modified_encrypted_file_buffer
            ) as decrypt:
                for plaintext_chunk in plaintext_chunks:
                    decrypt(len(plaintext_chunk))
