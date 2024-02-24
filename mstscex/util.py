"""Utility methods."""

import os
import random
import string
import sys
import tempfile
from types import TracebackType
from typing import Callable, Literal, Protocol, Self, TextIO, cast

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

LogLevelStr = Literal[
    "DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL"
]
LogLevel = LogLevelStr | int


class _LogContinuation(Protocol):
    def __call__(
        self, *values: object, end: str | None = "\n"
    ) -> "_LogContinuation":
        pass


class SimpleLogger:
    """Simple logger class."""

    LOG_LEVELS: dict[LogLevelStr, int] = {
        "DEBUG": 100,
        "INFO": 200,
        "NOTICE": 300,
        "WARNING": 400,
        "ERROR": 500,
        "CRITICAL": 600,
    }

    _level: LogLevel

    def __init__(self, level: LogLevel = "DEBUG"):
        """Create a simple logger."""
        self.level = level

    @property
    def level(self) -> LogLevel:
        """Get the current logging level."""
        return self._level

    @level.setter
    def level(self, val: LogLevel) -> None:
        """Set the current logging level."""
        self._level = val

    def can_log(self, level: LogLevel) -> bool:
        """Return whether the log level is at or above min_level."""
        if not isinstance(self.level, int):
            int_val = self.LOG_LEVELS[self.level]
        else:
            int_val = self.level

        if not isinstance(level, int):
            level = self.LOG_LEVELS[level]

        return level >= int_val

    def _no_log(
        self, *values: object, end: str | None = "\n"
    ) -> _LogContinuation:
        return self._no_log

    def log(
        self,
        level: LogLevel,
        value: Callable[[], object] | object,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        file: TextIO | None = sys.stderr,
    ) -> _LogContinuation:
        """Log to console."""
        if not self.can_log(level):
            return self._no_log

        if callable(value):
            value = value()

        level_str = ""

        if isinstance(level, str):
            level_str = level.upper()
        else:
            for level_name, level_val in sorted(
                self.LOG_LEVELS.items(), key=lambda x: x[1]
            ):
                if level_val < level:
                    level_str = level_name

        print(f"[{level_str}]", value, *values, sep, end, file, flush=True)

        return self._continue_with(sep, file)

    def _continue_with(
        self,
        sep: str | None = " ",
        file: TextIO | None = sys.stderr,
    ) -> _LogContinuation:
        def fn(*values: object, end: str | None = "\n") -> _LogContinuation:
            print(values, sep, end, file, flush=True)

            return fn

        return fn


_logger = SimpleLogger()

log = _logger.log


class TSPortalNameGenerator:
    """Create a TS web portal compatible filename."""

    _prefix: str
    _generated: dict[str, str]

    def __init__(self) -> None:
        """Create the name generator."""
        rand_digits = "".join(random.choice(string.digits) for i in range(5))

        self._prefix = os.path.join(
            tempfile.gettempdir(), f"TSPORTAL#{rand_digits}"
        )

        self._generated = {}

    def get_extension(self, ext: str) -> str:
        """Get the path to a generated file."""
        ext = ext.lower()

        ret = self._generated.get(ext)

        if ret:
            return ret

        ret = self._prefix + ext

        self._generated[ext] = ret

        return ret

    @property
    def rdp(self) -> str:
        """Get the path to the generated RDP file."""
        return self.get_extension(".rdp")

    def cleanup(self) -> None:
        """Delete all files generated."""
        for file in self._generated.values():
            try:
                os.unlink(file)
            except Exception:
                pass

        self._generated = {}

    def __enter__(self) -> Self:
        """Return self for context manager."""
        return self

    def __exit__(
        self,
        typ: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Cleanup all files for context manager."""
        self.cleanup()

        return False


def x509_sign(
    cert_raw: bytes,
    key_raw: bytes,
    data: bytes,
    get_pw_fn: Callable[[], str] | None = None,
) -> bytes:
    """Sign data with a key using X509 public-key crypto."""
    cert = x509.load_pem_x509_certificate(cert_raw)

    try:
        key = serialization.load_pem_private_key(key_raw, None)
    except ValueError:
        if get_pw_fn is not None:
            key = serialization.load_pem_private_key(key_raw, get_pw_fn())
        else:
            raise

    opts = [
        pkcs7.PKCS7Options.Binary,
        pkcs7.PKCS7Options.NoAttributes,
        pkcs7.PKCS7Options.DetachedSignature,
    ]

    signed = (
        pkcs7.PKCS7SignatureBuilder()
        .set_data(data)
        .add_signer(cert, key, hashes.SHA256())
        .sign(serialization.Encoding.DER, opts)
    )

    return cast(bytes, signed)
