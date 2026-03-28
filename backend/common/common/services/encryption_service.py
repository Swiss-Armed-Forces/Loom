from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Generator

from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto.Protocol.KDF import HKDF
from Crypto.Random import get_random_bytes
from pydantic import BaseModel, ConfigDict, Field, SecretBytes, field_validator

AES_KEY_LEN_BYTES = 32
AES_SALT_LEN_BYTES = 32
AES_NONCE_LEN_BYTES = 12
AES_MAC_LEN = 16
DEFAULT_ENCRYPTED_MAGIC_BYTES = b"LOOMENC"
FIXED_AES_KEY = ("0" * 32).encode()


class RandomSourceExhausted(Exception):
    pass


class RandomSource(ABC):
    @abstractmethod
    def get_random_bytes(self, size: int) -> bytes:
        pass


class FixedRandomSource(RandomSource):
    def __init__(self, _randsource: bytes):
        self._pos = 0
        self._randsource = _randsource

    def get_random_bytes(self, size: int) -> bytes:
        ret_bytes = self._randsource[self._pos : self._pos + size]
        if len(ret_bytes) != size:
            raise RandomSourceExhausted(
                f"Could not draw {size} more bytes from random source of len"
                f" {len(self._randsource)} bytes"
            )
        self._pos += size
        return ret_bytes


class SystemRandomSource(RandomSource):
    def get_random_bytes(self, size: int) -> bytes:
        return get_random_bytes(size)


class AESMasterKey(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    key: SecretBytes = Field(
        default_factory=lambda: SecretBytes(get_random_bytes(AES_KEY_LEN_BYTES)),
    )

    @field_validator("key")
    @classmethod
    def key_length_validator(cls, v: SecretBytes) -> SecretBytes:
        if len(v) != AES_KEY_LEN_BYTES:
            raise ValueError(
                f"Key of invalid length. Expected {AES_KEY_LEN_BYTES}, got {len(v)}"
            )
        return v

    @classmethod
    def from_string(cls, key: str):
        return cls(key=SecretBytes(key.encode()))

    @classmethod
    def from_random_source(cls, random_source: bytes | None = None):
        random_source_wrapper: SystemRandomSource | FixedRandomSource
        if random_source is None:
            random_source_wrapper = SystemRandomSource()
        else:
            random_source_wrapper = FixedRandomSource(random_source)

        key_bytes = bytes(
            byte1 ^ byte2
            for byte1, byte2 in zip(
                get_random_bytes(AES_KEY_LEN_BYTES),
                random_source_wrapper.get_random_bytes(AES_KEY_LEN_BYTES),
            )
        )
        return cls(key=SecretBytes(key_bytes))

    @classmethod
    def from_fixed_key(cls):
        return cls(key=FIXED_AES_KEY)


def _derive_key(master_key: AESMasterKey, salt: bytes) -> bytes:
    result = HKDF(master_key.key.get_secret_value(), AES_KEY_LEN_BYTES, salt, SHA512)
    if not isinstance(result, bytes):
        raise FileEncryptionServiceException("Invalid return type of HKDF function")
    return result


def _get_cipher(key: bytes, nonce: bytes) -> Any:
    return AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=AES_MAC_LEN)


class FileEncryptionServiceException(Exception):
    """Thrown by FileEncryptionService."""


class FileEncryptionService:
    """Handles ile encryption and decryption."""

    def __init__(
        self,
        master_key: AESMasterKey | None = None,
        magic_bytes: bytes = DEFAULT_ENCRYPTED_MAGIC_BYTES,
    ):
        self._master_key = master_key if master_key is not None else AESMasterKey()
        self._magic_bytes = magic_bytes

    def get_encrypted_stream(
        self, input_stream: Iterator[bytes]
    ) -> Generator[bytes, None, None]:
        salt = get_random_bytes(AES_SALT_LEN_BYTES)
        key = _derive_key(self._master_key, salt)
        nonce = get_random_bytes(AES_NONCE_LEN_BYTES)
        cipher = _get_cipher(key, nonce)

        # write file header
        yield self._magic_bytes
        yield salt
        yield nonce

        for chunk in input_stream:
            ciphertext = cipher.encrypt(chunk)
            yield ciphertext

        mac = cipher.digest()
        yield mac

    def get_decrypted_stream(
        self, input_stream: Iterator[bytes]
    ) -> Generator[bytes, None, None]:
        """Decrypt a stream of encrypted bytes.

        The input_stream must yield encrypted data starting with the header (magic
        bytes, salt, nonce) followed by ciphertext and ending with MAC.
        """
        # Buffer to accumulate input until we have enough for header/MAC parsing
        buffer = b""

        # Read header
        header_size = len(self._magic_bytes) + AES_SALT_LEN_BYTES + AES_NONCE_LEN_BYTES
        for chunk in input_stream:
            buffer += chunk
            if len(buffer) >= header_size + AES_MAC_LEN:
                break

        if len(buffer) < header_size + AES_MAC_LEN:
            raise FileEncryptionServiceException("Input too short")

        # Parse header
        magic = buffer[: len(self._magic_bytes)]
        if magic != self._magic_bytes:
            raise FileEncryptionServiceException(
                f"Magic bytes {str(self._magic_bytes)} not found"
            )

        salt = buffer[
            len(self._magic_bytes) : len(self._magic_bytes) + AES_SALT_LEN_BYTES
        ]
        nonce = buffer[len(self._magic_bytes) + AES_SALT_LEN_BYTES : header_size]

        key = _derive_key(self._master_key, salt)
        cipher = _get_cipher(key, nonce)

        # Process remaining data, keeping last AES_MAC_LEN bytes as potential MAC
        buffer = buffer[header_size:]

        for chunk in input_stream:
            buffer += chunk
            # Yield all but the last AES_MAC_LEN bytes (which might be MAC)
            if len(buffer) > AES_MAC_LEN:
                to_decrypt = buffer[:-AES_MAC_LEN]
                buffer = buffer[-AES_MAC_LEN:]
                if to_decrypt:
                    yield cipher.decrypt(to_decrypt)

        # Final chunk: buffer contains MAC
        if len(buffer) < AES_MAC_LEN:
            raise FileEncryptionServiceException(f"MAC too short: {len(buffer)}")

        mac = buffer[-AES_MAC_LEN:]
        remaining_ciphertext = buffer[:-AES_MAC_LEN]
        if remaining_ciphertext:
            yield cipher.decrypt(remaining_ciphertext)

        cipher.verify(mac)
