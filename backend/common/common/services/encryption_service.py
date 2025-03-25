from abc import ABC, abstractmethod
from contextlib import contextmanager
from tempfile import SpooledTemporaryFile
from typing import Any, BinaryIO, Generator

from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto.Protocol.KDF import HKDF
from Crypto.Random import get_random_bytes
from gridfs import GridIn
from pydantic import BaseModel, ConfigDict, Field, SecretBytes, field_validator
from typing_extensions import Protocol

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


class EncryptorProtocol(Protocol):
    def __call__(self, data: bytes):
        pass


class DecryptorProtocol(Protocol):
    def __call__(self, size: int = -1) -> bytes:
        pass


class FileEncryptionService:
    """Handles ile encryption and decryption."""

    def __init__(
        self,
        master_key: AESMasterKey | None = None,
        magic_bytes: bytes = DEFAULT_ENCRYPTED_MAGIC_BYTES,
    ):
        self._master_key = master_key if master_key is not None else AESMasterKey()
        self._magic_bytes = magic_bytes

    @contextmanager
    def get_encryptor(
        self, dst: BinaryIO | GridIn | SpooledTemporaryFile[bytes]
    ) -> Generator[EncryptorProtocol, None, None]:
        salt = get_random_bytes(AES_SALT_LEN_BYTES)
        key = _derive_key(self._master_key, salt)
        nonce = get_random_bytes(AES_NONCE_LEN_BYTES)
        cipher = _get_cipher(key, nonce)

        def encrypt(data: bytes):
            ciphertext = cipher.encrypt(data)
            dst.write(ciphertext)

        # write file header
        dst.write(self._magic_bytes)
        dst.write(salt)
        dst.write(nonce)

        yield encrypt

        mac = cipher.digest()
        dst.write(mac)

    @contextmanager
    def get_decryptor(
        self, src: BinaryIO | GridIn | SpooledTemporaryFile[bytes]
    ) -> Generator[DecryptorProtocol, None, None]:
        magic = src.read(len(self._magic_bytes))
        if magic != self._magic_bytes:
            raise FileEncryptionServiceException(
                f"Magic bytes {str(self._magic_bytes)} not found"
            )

        salt = src.read(AES_SALT_LEN_BYTES)
        if len(salt) != AES_SALT_LEN_BYTES:
            raise FileEncryptionServiceException(
                f"Failed reading salt. Expected {AES_SALT_LEN_BYTES} bytes, got"
                f" {len(salt)}"
            )
        key = _derive_key(self._master_key, salt)
        nonce = src.read(AES_NONCE_LEN_BYTES)
        if len(nonce) != AES_NONCE_LEN_BYTES:
            raise FileEncryptionServiceException(
                f"Failed reading nonce. Expected {AES_NONCE_LEN_BYTES} bytes, got"
                f" {len(nonce)}"
            )
        cipher = _get_cipher(key, nonce)

        mac = src.read(AES_MAC_LEN)
        if len(mac) != AES_MAC_LEN:
            raise FileEncryptionServiceException(
                f"Failed reading mac. Expected {AES_MAC_LEN} bytes, got {len(mac)}"
            )

        def decrypt(size: int = -1) -> bytes:
            nonlocal mac

            # ciphertext is always previous mac and new data
            ciphertext = mac[:size] if size >= 0 else mac
            ciphertext += src.read(size - len(ciphertext)) if size >= 0 else src.read()

            # always also read possible new mac
            mac = mac[size:] if size >= 0 else b""
            mac += src.read(AES_MAC_LEN - len(mac)) if size >= 0 else b""

            # is mac long enough?
            mac_remaining = AES_MAC_LEN - len(mac)
            if mac_remaining > 0:
                # no: clip some data from ciphertext
                mac = ciphertext[-mac_remaining:]
                ciphertext = ciphertext[:-mac_remaining]

            plaintext = cipher.decrypt(ciphertext)
            return plaintext

        yield decrypt

        cipher.verify(mac)
