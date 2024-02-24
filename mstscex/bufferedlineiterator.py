"""Buffered line iterator and related."""

from typing import Generator


class BufferedLineIterator:
    """Iterable line buffer."""

    _buffer: str
    _keepends: bool

    def __init__(self, keepends: bool = False):
        """Create an iterable line buffer.

        Keyword arguments:
        keepends -- keep line break on yielded strings (default False)
        """
        self._buffer = ""
        self._keepends = keepends

    def push(self, data: str) -> None:
        """Add data to line buffer."""
        self._buffer += data

    @staticmethod
    def is_line_break(ch: str) -> bool:
        """Determine if a character is a line break."""
        return (
            ch == "\u000a"
            or ch == "\u000b"
            or ch == "\u000c"
            or ch == "\u000d"
            or ch == "\u001c"
            or ch == "\u001d"
            or ch == "\u001e"
            or ch == "\u0085"
            or ch == "\u2028"
            or ch == "\u2029"
        )

    def __iter__(self) -> Generator[str, None, None]:
        """Return each line in the current buffer."""
        buffer_len = len(self._buffer)

        i = 0
        j = 0

        try:
            while i < buffer_len:
                while i < buffer_len and not self.is_line_break(
                    self._buffer[i]
                ):
                    i += 1

                if i >= buffer_len:
                    # no line breaks yet
                    continue

                # treat CRLF as one line break
                eol = i

                if i < buffer_len:
                    if (
                        self._buffer[i] == "\r"
                        and i + 1 < buffer_len
                        and self._buffer[i + 1] == "\n"
                    ):
                        i += 2
                    else:
                        i += 1

                    if self._keepends:
                        eol = i

                yield self._buffer[j:eol]

                j = i
        finally:
            self._buffer = self._buffer[j:]

    @property
    def buffer(self) -> str:
        """Get the current buffer."""
        return self._buffer
